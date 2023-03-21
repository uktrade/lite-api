from django.db.models import Q
from django.http import JsonResponse
from rest_framework import status
from rest_framework.exceptions import ErrorDetail

from api.applications.serializers.advice import AdviceCreateSerializer, AdviceUpdateSerializer
from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.cases.enums import AdviceLevel, AdviceType
from api.cases.generated_documents.models import GeneratedCaseDocument
from api.cases.libraries.get_case import get_case
from api.cases.models import Advice, GoodCountryDecision
from api.core import constants
from api.core.constants import GovPermissions
from api.core.permissions import assert_user_has_permission
from api.flags.enums import SystemFlags
from api.flags.models import Flag
from lite_content.lite_api import strings
from api.staticdata.statuses.enums import CaseStatusEnum


def check_if_user_cannot_manage_team_advice(case, user):
    if constants.GovPermissions.MANAGE_TEAM_CONFIRM_OWN_ADVICE.name not in user.role.permissions.values_list(
        "id", flat=True
    ):
        assert_user_has_permission(user, constants.GovPermissions.MANAGE_TEAM_ADVICE)


def check_if_final_advice_exists(case):
    if Advice.objects.get_final_advice(case=case):
        return JsonResponse({"errors": "Final advice already exists for this case"}, status=status.HTTP_400_BAD_REQUEST)


def check_refusal_errors(advice):
    if advice.get("type") and advice["type"].lower() == AdviceType.REFUSE and not advice["text"]:
        return {"text": [ErrorDetail(string=strings.Cases.ADVICE_REFUSAL_ERROR, code="blank")]}
    return None


def update_good_country_decisions(data):
    """
    Delete any GoodCountryDecision's that may now be invalid
    (the country or goods type are no longer approved)
    """
    refused_good_types_ids = [
        advice["goods_type"]
        for advice in data
        if advice.get("goods_type") and advice["type"] not in [AdviceType.APPROVE, AdviceType.PROVISO]
    ]
    refused_country_ids = [
        advice["country"]
        for advice in data
        if advice.get("country") and advice["type"] not in [AdviceType.APPROVE, AdviceType.PROVISO]
    ]
    GoodCountryDecision.objects.filter(
        Q(country_id__in=refused_country_ids) | Q(goods_type_id__in=refused_good_types_ids)
    ).delete()


def post_advice(request, case, level, team=False):
    if CaseStatusEnum.is_terminal(case.status.status):
        return JsonResponse(
            data={"errors": [strings.Applications.Generic.TERMINAL_CASE_CANNOT_PERFORM_OPERATION_ERROR]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    data = request.data

    # Update the case and user in each piece of advice
    refusal_error = False
    for advice in data:
        advice["level"] = level
        advice["case"] = str(case.id)
        advice["user"] = str(request.user.pk)
        if team:
            advice["team"] = str(request.user.govuser.team.id)
        if not refusal_error:
            refusal_error = check_refusal_errors(advice)

    # we only need to know if the user has the permission if not final advice
    footnote_permission = (
        request.user.govuser.has_permission(GovPermissions.MAINTAIN_FOOTNOTES) and level != AdviceLevel.FINAL
    )

    serializer = AdviceCreateSerializer(data=data, many=True, context={"footnote_permission": footnote_permission})

    if serializer.is_valid() and not refusal_error:
        serializer.save()

        audit_verbs = {
            AdviceLevel.USER: AuditType.CREATED_USER_ADVICE,
            AdviceLevel.TEAM: AuditType.REVIEW_COMBINE_ADVICE,
        }

        department = request.user.govuser.team.department

        if department is not None:
            department = department.name
        else:
            department = "department"

        if level in audit_verbs:
            audit_trail_service.create(
                actor=request.user, verb=audit_verbs[level], target=case, payload={"department": department}
            )

        if level == AdviceLevel.FINAL:
            # Remove GoodCountryDecision if changing approve decision for applicable country/goods type
            update_good_country_decisions(data)
            # Remove outdated draft decision documents if advice changes
            GeneratedCaseDocument.objects.filter(
                case_id=case.id, advice_type__isnull=False, visible_to_exporter=False
            ).delete()
        return JsonResponse({"advice": serializer.data}, status=status.HTTP_201_CREATED)

    errors = {}
    if serializer.errors:
        errors.update(serializer.errors[0])

    if refusal_error:
        errors.update(refusal_error)
    return JsonResponse({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)


def update_advice(request, case, level):
    if CaseStatusEnum.is_terminal(case.status.status):
        return JsonResponse(
            data={"errors": [strings.Applications.Generic.TERMINAL_CASE_CANNOT_PERFORM_OPERATION_ERROR]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    for item in request.data:
        current_level = item.get("level")
        if current_level and current_level != level:
            return JsonResponse(
                data={"errors": ["Advice level cannot be updated once it is created"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

    # we only need to know if the user has the permission if not final advice
    footnote_permission = (
        request.user.govuser.has_permission(GovPermissions.MAINTAIN_FOOTNOTES) and level != AdviceLevel.FINAL
    )

    data = request.data
    advice_ids = [item["id"] for item in data]
    serializer = AdviceUpdateSerializer(
        Advice.objects.filter(id__in=advice_ids),
        data=data,
        partial=True,
        many=True,
        context={"footnote_permission": footnote_permission},
    )
    if not serializer.is_valid():
        return JsonResponse({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()

    return JsonResponse({"advice": serializer.data}, status=status.HTTP_200_OK)


def case_advice_contains_refusal(case_id):
    case = get_case(case_id)
    team_advice = Advice.objects.filter(case=case)
    flag = Flag.objects.get(id=SystemFlags.REFUSAL_FLAG_ID)

    refuse_advice_found = False

    for advice in team_advice:
        if advice.type.lower() == "refuse":
            refuse_advice_found = True
            if flag not in case.flags.all():
                case.flags.add(flag)
                break

    if not refuse_advice_found:
        if flag in case.flags.all():
            case.flags.remove(flag)
