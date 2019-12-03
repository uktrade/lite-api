from lite_content.lite_api import strings
from django.http import JsonResponse
from rest_framework import status
from rest_framework.exceptions import ErrorDetail

from applications.models import BaseApplication
from cases.libraries.get_case import get_case
from cases.models import FinalAdvice, TeamAdvice, Advice
from conf.constants import Permissions
from conf.permissions import assert_user_has_permission
from flags.enums import SystemFlags
from flags.models import Flag
from lite_content.lite_api.strings import ADVICE_POST_TEAM_ADVICE_WHEN_USER_ADVICE_EXISTS_ERROR
from static.statuses.enums import CaseStatusEnum
from lite_content.lite_api import strings


def check_if_user_cannot_manage_team_advice(case, user):
    if Permissions.MANAGE_TEAM_CONFIRM_OWN_ADVICE not in user.role.permissions.values_list("id", flat=True):
        assert_user_has_permission(user, Permissions.MANAGE_TEAM_ADVICE)

        if Advice.objects.filter(case=case, user=user).exists():
            return JsonResponse(
                {"errors": ADVICE_POST_TEAM_ADVICE_WHEN_USER_ADVICE_EXISTS_ERROR}, status=status.HTTP_403_FORBIDDEN,
            )


def check_if_final_advice_exists(case):
    if FinalAdvice.objects.filter(case=case):
        return JsonResponse(
            {"errors": "Final advice already exists for this case"}, status=status.HTTP_400_BAD_REQUEST,
        )


def check_if_team_advice_exists(case, user):
    if TeamAdvice.objects.filter(case=case, team=user.team):
        return JsonResponse(
            {"errors": "Team advice from your team already exists for this case"}, status=status.HTTP_400_BAD_REQUEST,
        )


def check_refusal_errors(advice):
    if advice["type"].lower() == "refuse" and not advice["text"]:
        return {"text": [ErrorDetail(string=strings.Cases.ADVICE_REFUSAL_ERROR, code="blank")]}
    return None


def post_advice(request, case, serializer_object, team=False):
    application = BaseApplication.objects.get(id=case.application_id)

    if CaseStatusEnum.is_terminal(application.status.status):
        return JsonResponse(
            data={"errors": [strings.TERMINAL_CASE_CANNOT_PERFORM_OPERATION_ERROR]}, status=status.HTTP_400_BAD_REQUEST,
        )

    data = request.data

    # Update the case and user in each piece of advice
    refusal_error = False
    for advice in data:
        advice["case"] = str(case.id)
        advice["user"] = str(request.user.id)
        if team:
            advice["team"] = str(request.user.team.id)
        if not refusal_error:
            refusal_error = check_refusal_errors(advice)

    serializer = serializer_object(data=data, many=True)

    if serializer.is_valid() and not refusal_error:
        serializer.save()
        return JsonResponse({"advice": serializer.data}, status=status.HTTP_201_CREATED)

    errors = [{}]
    if serializer.errors:
        errors[0].update(serializer.errors[0])

    if refusal_error:
        errors[0].update(refusal_error)
    return JsonResponse({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)


def case_advice_contains_refusal(case_id):
    case = get_case(case_id)
    team_advice = TeamAdvice.objects.filter(case=case)
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
