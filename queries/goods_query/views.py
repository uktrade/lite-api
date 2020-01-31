from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from applications.libraries.application_helpers import can_status_can_be_set_by_gov_user
from audit_trail import service as audit_trail_service
from audit_trail.payload import AuditType
from cases.enums import CaseTypeEnum
from cases.generated_documents.models import GeneratedCaseDocument
from cases.generated_documents.serializers import GeneratedCaseDocumentExporterSerializer
from conf import constants
from conf.authentication import ExporterAuthentication, GovAuthentication
from conf.helpers import str_to_bool
from conf.permissions import assert_user_has_permission
from flags.enums import SystemFlags
from flags.models import Flag
from goods.enums import GoodStatus, GoodControlled, GoodPvGraded
from goods.libraries.get_goods import get_good
from goods.models import Good
from goods.serializers import ClcControlGoodSerializer
from lite_content.lite_api import strings
from queries.goods_query.models import GoodsQuery
from queries.goods_query.serializers import PVGradingResponseSerializer
from queries.helpers import get_exporter_query
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from users.models import UserOrganisationRelationship


class GoodsQueriesCreate(APIView):
    """
    Create a Goods Query which can contain a CLC part and a PV Grading part
    """

    authentication_classes = (ExporterAuthentication,)

    @staticmethod
    def _check_request_for_errors(good: Good, is_clc_required: bool, is_pv_grading_required: bool):
        errors = []
        if GoodsQuery.objects.filter(good_id=good).exists():
            errors += [strings.GoodsQuery.A_QUERY_ALREADY_EXISTS_FOR_THIS_GOOD_ERROR]

        if good.status != GoodStatus.DRAFT:
            errors += [{"status": strings.GoodsQuery.GOOD_DRAFT_STATUS_REQUIRED_ERROR}]

        if not (is_clc_required or is_pv_grading_required):
            errors += [strings.GoodsQuery.GOOD_CLC_UNSURE_OR_PV_REQUIRED_ERROR]

        return errors

    def post(self, request):
        """
        Create a new GoodsQuery case instance
        """
        data = request.data
        good = get_good(data["good_id"])

        data["organisation"] = request.user.organisation

        is_clc_required = good.is_good_controlled == GoodControlled.UNSURE
        is_pv_grading_required = good.is_pv_graded == GoodPvGraded.GRADING_REQUIRED

        errors = self._check_request_for_errors(good, is_clc_required, is_pv_grading_required)
        if errors:
            return JsonResponse(data={"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        good.status = GoodStatus.QUERY
        good.control_code = data.get("clc_control_code", None)

        goods_query = GoodsQuery.objects.create(
            clc_raised_reasons=data.get("clc_raised_reasons"),
            pv_grading_raised_reasons=data.get("pv_grading_raised_reasons"),
            good=good,
            organisation=data["organisation"],
            type=CaseTypeEnum.GOODS_QUERY,
            status=get_case_status_by_status(CaseStatusEnum.SUBMITTED),
        )

        # attach flags based on what's required
        if is_clc_required:
            flag = Flag.objects.get(id=SystemFlags.GOOD_CLC_QUERY_ID)
            goods_query.flags.add(flag)
        if is_pv_grading_required:
            flag = Flag.objects.get(id=SystemFlags.GOOD_PV_GRADING_QUERY_ID)
            goods_query.flags.add(flag)

        good.save()
        goods_query.save()

        return JsonResponse(data={"id": goods_query.id}, status=status.HTTP_201_CREATED)


class GoodQueryCLCResponse(APIView):
    """
    Respond to the CLC query of a Goods Query
    """

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

        data = request.data

        clc_good_serializer = ClcControlGoodSerializer(query.good, data=data)

        if clc_good_serializer.is_valid():
            if not str_to_bool(data.get("validate_only")):
                previous_control_code = (
                    query.good.control_code if query.good.control_code else strings.Goods.GOOD_NO_CONTROL_CODE
                )

                clc_good_serializer.save()
                query.flags.remove(Flag.objects.get(id=SystemFlags.GOOD_CLC_QUERY_ID))
                query.clc_responded = True
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


class GoodQueryPVGradingResponse(APIView):
    """
    Respond to the PV Grading query of a Goods Query
    """

    authentication_classes = (GovAuthentication,)

    @transaction.atomic
    def put(self, request, pk):
        """ Respond to a control list classification."""
        assert_user_has_permission(request.user, constants.GovPermissions.RESPOND_PV_GRADING)

        query = get_exporter_query(pk)
        if CaseStatusEnum.is_terminal(query.status.status):
            return JsonResponse(
                data={"errors": [strings.Applications.TERMINAL_CASE_CANNOT_PERFORM_OPERATION_ERROR]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = request.data

        pv_grading_good_serializer = PVGradingResponseSerializer(data=data)

        if pv_grading_good_serializer.is_valid():
            if not str_to_bool(data.get("validate_only")):
                pv_grading = pv_grading_good_serializer.save()
                self.update_query_and_good(query, data, pv_grading)
                self.generate_audit_trail(request.user, query)

                # Send a notification to the user
                for user_relationship in UserOrganisationRelationship.objects.filter(organisation=query.organisation):
                    user_relationship.send_notification(content_object=query, case=query)

                return JsonResponse(
                    data={"pv_grading_query": pv_grading_good_serializer.data}, status=status.HTTP_200_OK,
                )

            return JsonResponse(data={"pv_grading_query": data}, status=status.HTTP_200_OK)

        return JsonResponse(data={"errors": pv_grading_good_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def update_query_and_good(self, query, data, pv_grading):
        query.good.is_pv_graded = GoodPvGraded.YES
        query.good.pv_grading_details = pv_grading
        query.good.grading_comment = data.get("comment", "")
        query.good.save()
        query.flags.remove(Flag.objects.get(id=SystemFlags.GOOD_PV_GRADING_QUERY_ID))
        query.pv_grading_responded = True
        query.save()

    def generate_audit_trail(self, user, query):
        grading = (
            f"{query.good.pv_grading_details.prefix} {query.good.pv_grading_details.grading} "
            f"{query.good.pv_grading_details.suffix}"
        )

        audit_trail_service.create(
            actor=user,
            verb=AuditType.PV_GRADING_RESPONSE,
            action_object=query.good,
            target=query.get_case(),
            payload={"grading": grading},
        )


class GoodQueryManageStatus(APIView):
    """
    Modify the status of a Goods Query
    """

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
            payload={"status": CaseStatusEnum.get_text(new_status)},
        )

        return JsonResponse(data={}, status=status.HTTP_200_OK)


class GeneratedDocuments(APIView):
    authentication_classes = (ExporterAuthentication,)
    serializer_class = GeneratedCaseDocumentExporterSerializer
    queryset = GeneratedCaseDocument

    def get(self, request, pk):
        dataset = self.queryset.objects.filter(case__id=pk)
        data = self.serializer_class(dataset, many=True).data
        return JsonResponse(data={"generated_documents": data}, status=status.HTTP_200_OK)
