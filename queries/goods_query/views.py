import json

from django.http import JsonResponse, Http404
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from applications.libraries.application_helpers import can_status_can_be_set_by_gov_user
from audit_trail import service as audit_trail_service
from audit_trail.payload import AuditType
from cases.enums import CaseTypeEnum
from conf import constants
from conf.authentication import ExporterAuthentication, GovAuthentication
from conf.helpers import str_to_bool
from conf.permissions import assert_user_has_permission
from flags.enums import SystemFlags
from goods.enums import GoodStatus
from goods.libraries.get_goods import get_good
from goods.serializers import ClcControlGoodSerializer
from lite_content.lite_api import strings
from queries.goods_query.models import GoodsQuery
from queries.helpers import get_exporter_query
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from users.models import UserOrganisationRelationship


# TODO: 1027 generate GoodsQuery with correct flags
class GoodsQueriesCreate(APIView):
    authentication_classes = (ExporterAuthentication,)

    def post(self, request):
        """
        Create a new CLC query case instance
        """
        data = JSONParser().parse(request)
        good = get_good(data["good_id"])
        data["organisation"] = request.user.organisation

        # A CLC/PV Query can only be created if the good is in draft status
        if good.status != GoodStatus.DRAFT:
            raise Http404

        good.status = GoodStatus.CLC_QUERY
        good.control_code = data.get("not_sure_details_control_code")

        clc_query = GoodsQuery.objects.create(
            clc_=data.get("not_sure_details_details"),
            good=good,
            organisation=data["organisation"],
            type=CaseTypeEnum.CLC_QUERY,
            status=get_case_status_by_status(CaseStatusEnum.SUBMITTED),
        )

        good.save()
        clc_query.save()

        return JsonResponse(data={"id": clc_query.id}, status=status.HTTP_201_CREATED)


# TODO: 1027 update to remove flag instead of close case
class GoodQueryCLCResponse(APIView):
    authentication_classes = (GovAuthentication,)

    def put(self, request, pk):
        """ Respond to a control list classification."""
        assert_user_has_permission(request.user, constants.GovPermissions.REVIEW_GOODS)

        query = get_exporter_query(pk)
        if CaseStatusEnum.is_terminal(query.status.status):
            return JsonResponse(
                data={"errors": [strings.Applications.TERMINAL_CASE_CANNOT_PERFORM_OPERATION_ERROR]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = json.loads(request.body)

        clc_good_serializer = ClcControlGoodSerializer(query.good, data=data)

        if clc_good_serializer.is_valid():
            if not str_to_bool(data.get("validate_only")):
                previous_control_code = (
                    query.good.control_code if query.good.control_code else strings.Goods.GOOD_NO_CONTROL_CODE
                )

                clc_good_serializer.save()
                query.status = get_case_status_by_status(CaseStatusEnum.FINALISED)
                query.save()

                new_control_code = strings.Goods.GOOD_NO_CONTROL_CODE

                if str_to_bool(clc_good_serializer.validated_data.get("is_good_controlled")):
                    new_control_code = clc_good_serializer.validated_data.get(
                        "control_code", strings.Goods.GOOD_NO_CONTROL_CODE
                    )

                if new_control_code != previous_control_code:
                    audit_trail_service.create(
                        actor=request.user,
                        verb=AuditType.GOOD_REVIEWED,
                        action_object=query.good,
                        target=query.get_case(),
                        payload={
                            "good_name": query.good.description,
                            "old_control_code": previous_control_code,
                            "new_control_code": new_control_code,
                        },
                    )

                audit_trail_service.create(
                    actor=request.user, verb=AuditType.CLC_RESPONSE, action_object=query.good, target=query.get_case(),
                )

                # Send a notification to the user
                for user_relationship in UserOrganisationRelationship.objects.filter(organisation=query.organisation):
                    user_relationship.send_notification(content_object=query, case=query)

                return JsonResponse(
                    data={"control_list_classification_query": clc_good_serializer.data}, status=status.HTTP_200_OK
                )

            return JsonResponse(data={"control_list_classification_query": data}, status=status.HTTP_200_OK)

        return JsonResponse(data={"errors": clc_good_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class GoodQueryManageStatus(APIView):
    authentication_classes = (GovAuthentication,)

    def put(self, request, pk):
        query = get_exporter_query(pk)
        new_status = request.data.get("status")

        if not can_status_can_be_set_by_gov_user(request.user, query.status.status, new_status):
            return JsonResponse(
                data={"errors": ["Status cannot be set by Gov user."]}, status=status.HTTP_400_BAD_REQUEST
            )

        query.status = get_case_status_by_status(new_status)
        query.save()

        audit_trail_service.create(
            actor=request.user,
            verb=AuditType.UPDATED_STATUS,
            target=query.get_case(),
            payload={"status": CaseStatusEnum.human_readable(new_status)},
        )

        return JsonResponse(data={}, status=status.HTTP_200_OK)
