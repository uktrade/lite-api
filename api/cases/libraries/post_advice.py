from django.http import JsonResponse
from rest_framework import status
from rest_framework.exceptions import ErrorDetail

from api.applications.libraries.get_applications import get_application
from api.applications.serializers.advice import AdviceCreateSerializer, AdviceUpdateSerializer
from api.applications.views.helpers.advice import (
    mark_lu_rejected_countersignatures_as_invalid,
    remove_countersign_process_flags,
)
from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.cases.enums import AdviceLevel, AdviceType
from api.cases.generated_documents.models import GeneratedCaseDocument
from api.cases.libraries.get_case import get_case
from api.cases.models import Advice
from api.core import constants
from api.core.constants import GovPermissions
from api.core.permissions import assert_user_has_permission
from api.flags.enums import SystemFlags
from api.flags.models import Flag
from lite_content.lite_api import strings
from api.staticdata.statuses.enums import CaseStatusEnum
from api.teams.enums import TeamIdEnum
from api.teams.models import Team


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
            # Remove outdated draft decision documents if advice changes
            GeneratedCaseDocument.objects.filter(
                case_id=case.id, advice_type__isnull=False, visible_to_exporter=False
            ).delete()

            if data[0].get("is_refusal_note", False):
                audit_lu_countersigning(AuditType.LU_CREATE_MEETING_NOTE, data[0]["type"], data, case, request)

            advice_type = data[0]["type"]
            audit_lu_countersigning(AuditType.LU_ADVICE, advice_type, data, case, request)
            # Refused applications do not need to go through LU countersign - so remove the countersign flags now
            if advice_type == AdviceType.REFUSE:
                application = get_application(case.id)
                remove_countersign_process_flags(application, case)
                audit_refusal_criteria(AuditType.CREATE_REFUSAL_CRITERIA, advice_type, data[0], case, request)

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
    advice_to_update = Advice.objects.filter(id__in=advice_ids)

    serializer = AdviceUpdateSerializer(
        advice_to_update,
        data=data,
        partial=True,
        many=True,
        context={"footnote_permission": footnote_permission},
    )
    if not serializer.is_valid():
        return JsonResponse({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()

    mark_lu_rejected_countersignatures_as_invalid(case, request.user)

    advice_type = advice_to_update.first().type

    if advice_to_update.first().is_refusal_note:
        audit_lu_countersigning(AuditType.LU_EDIT_MEETING_NOTE, advice_type, data, case, request)
        audit_refusal_criteria(AuditType.CREATE_REFUSAL_CRITERIA, advice_type, data[0], case, request)
    else:
        audit_lu_countersigning(AuditType.LU_EDIT_ADVICE, advice_to_update.first().type, data, case, request)

    advice_type = advice_to_update.first().type
    # Refused applications do not need to go through LU countersign - so remove the countersign flags now
    if advice_type == AdviceType.REFUSE and level == AdviceLevel.FINAL:
        application = get_application(case.id)
        remove_countersign_process_flags(application, case)

    return JsonResponse({"advice": serializer.data}, status=status.HTTP_200_OK)


def audit_lu_countersigning(audit_type, advice_type, data, case, request):
    ADVICE_AUDIT_LIST = {
        AuditType.LU_EDIT_ADVICE,
        AuditType.LU_EDIT_MEETING_NOTE,
        AuditType.LU_CREATE_MEETING_NOTE,
    }

    if request.user.govuser.team == Team.objects.get(id=TeamIdEnum.LICENSING_UNIT) and advice_type in [
        AdviceType.APPROVE,
        AdviceType.REFUSE,
        AdviceType.PROVISO,
    ]:
        audit_payload = {
            "firstname": request.user.first_name,  # /PS-IGNORE
            "lastname": request.user.last_name,  # /PS-IGNORE
            "advice_type": advice_type,
        }
        if advice_type == AdviceType.PROVISO:
            audit_payload["additional_text"] = data[0]["proviso"]
        elif audit_type in ADVICE_AUDIT_LIST:
            audit_payload["additional_text"] = data[0]["text"]

        audit_trail_service.create(actor=request.user, verb=audit_type, target=case, payload=audit_payload)


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


def audit_refusal_criteria(audit_type, advice_type, data, case, request):
    audit_payload = {
        "firstname": request.user.first_name,  # /PS-IGNORE
        "lastname": request.user.last_name,  # /PS-IGNORE
        "advice_type": advice_type,
    }
    if data.get("denial_reasons"):
        audit_payload["additional_text"] = ", ".join(data["denial_reasons"]) + "."

    audit_trail_service.create(actor=request.user, verb=audit_type, target=case, payload=audit_payload)
