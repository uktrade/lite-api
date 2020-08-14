import django.utils.timezone
from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from audit_trail import service as audit_trail_service
from audit_trail.enums import AuditType
from cases.enums import CaseTypeEnum
from api.conf import constants
from api.conf.authentication import ExporterAuthentication, GovAuthentication
from api.conf.helpers import str_to_bool
from api.conf.permissions import assert_user_has_permission
from api.flags.enums import SystemFlags
from api.flags.models import Flag
from api.goods.enums import GoodStatus, GoodControlled, GoodPvGraded
from api.goods.libraries.get_goods import get_good
from api.goods.libraries.get_pv_grading import get_pv_grading_value_from_key
from api.goods.models import Good
from api.goods.serializers import ClcControlGoodSerializer
from lite_content.lite_api import strings
from api.organisations.libraries.get_organisation import get_request_user_organisation_id
from queries.goods_query.helpers import get_starting_status
from queries.goods_query.models import GoodsQuery
from queries.goods_query.serializers import PVGradingResponseSerializer
from queries.helpers import get_exporter_query
from static.statuses.enums import CaseStatusEnum
from api.users.models import UserOrganisationRelationship
from workflow.flagging_rules_automation import apply_flagging_rules_to_case


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

        data["organisation"] = get_request_user_organisation_id(request)

        is_clc_required = good.is_good_controlled == GoodControlled.UNSURE
        is_pv_grading_required = good.is_pv_graded == GoodPvGraded.GRADING_REQUIRED

        errors = self._check_request_for_errors(good, is_clc_required, is_pv_grading_required)
        if errors:
            return JsonResponse(data={"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        good.status = GoodStatus.QUERY

        goods_query = GoodsQuery.objects.create(
            clc_control_list_entry=data.get("clc_control_list_entry"),
            clc_raised_reasons=data.get("clc_raised_reasons"),
            pv_grading_raised_reasons=data.get("pv_grading_raised_reasons"),
            good=good,
            organisation_id=data["organisation"],
            case_type_id=CaseTypeEnum.GOODS.id,
            status=get_starting_status(is_clc_required),
            submitted_at=django.utils.timezone.now(),
            submitted_by=request.user,
        )

        # attach flags based on what's required
        if is_clc_required:
            flag = Flag.objects.get(id=SystemFlags.GOOD_CLC_QUERY_ID)
            goods_query.flags.add(flag)
            goods_query.clc_responded = False
        if is_pv_grading_required:
            flag = Flag.objects.get(id=SystemFlags.GOOD_PV_GRADING_QUERY_ID)
            goods_query.flags.add(flag)
            goods_query.pv_grading_responded = False

        good.save()
        goods_query.save()

        audit_trail_service.create(
            actor=request.user,
            verb=AuditType.CREATED,
            action_object=goods_query.get_case(),
            payload={"status": {"new": goods_query.status.status}},
        )

        apply_flagging_rules_to_case(goods_query)

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
                data={"errors": [strings.Applications.Generic.TERMINAL_CASE_CANNOT_PERFORM_OPERATION_ERROR]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = request.data

        clc_good_serializer = ClcControlGoodSerializer(query.good, data=data)

        if clc_good_serializer.is_valid():
            if not str_to_bool(data.get("validate_only")):
                previous_control_list_entries = list(
                    query.good.control_list_entries.values_list("rating", flat=True)
                ) or [strings.Goods.GOOD_NO_CONTROL_CODE]

                clc_good_serializer.save()
                query.clc_responded = True
                query.save()

                new_control_list_entries = [strings.Goods.GOOD_NO_CONTROL_CODE]

                if str_to_bool(clc_good_serializer.validated_data.get("is_good_controlled")):
                    new_control_list_entries = clc_good_serializer.validated_data.get(
                        "control_list_entries", [strings.Goods.GOOD_NO_CONTROL_CODE]
                    )

                    if strings.Goods.GOOD_NO_CONTROL_CODE not in new_control_list_entries:
                        new_control_list_entries = [clc.rating for clc in new_control_list_entries]

                if new_control_list_entries != previous_control_list_entries:
                    audit_trail_service.create(
                        actor=request.user,
                        verb=AuditType.GOOD_REVIEWED,
                        action_object=query.good,
                        target=query.get_case(),
                        payload={
                            "good_name": query.good.description,
                            "old_control_list_entry": previous_control_list_entries,
                            "new_control_list_entry": new_control_list_entries,
                        },
                    )

                flag = Flag.objects.get(id=SystemFlags.GOOD_CLC_QUERY_ID)
                query.good.flags.remove(flag)
                query.good.status = GoodStatus.VERIFIED
                query.good.save()
                apply_flagging_rules_to_case(query)

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
                data={"errors": [strings.Applications.Generic.TERMINAL_CASE_CANNOT_PERFORM_OPERATION_ERROR]},
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
        query.pv_grading_responded = True
        query.save()

    def generate_audit_trail(self, user, query):
        grading = (
            f"{query.good.pv_grading_details.prefix} "
            f"{get_pv_grading_value_from_key(query.good.pv_grading_details.grading)} "
            f"{query.good.pv_grading_details.suffix}"
        )

        audit_trail_service.create(
            actor=user,
            verb=AuditType.PV_GRADING_RESPONSE,
            action_object=query.good,
            target=query.get_case(),
            payload={"grading": grading},
        )
