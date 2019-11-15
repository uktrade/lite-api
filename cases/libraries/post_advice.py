from django.http import JsonResponse
from rest_framework import status
from rest_framework.exceptions import ErrorDetail

from cases.models import FinalAdvice, TeamAdvice, Advice
from conf.constants import Permissions
from conf.permissions import assert_user_has_permission
from content_strings.strings import get_string


def assert_user_can_create_or_edit_team_advice_on_case(case, user):
    if not assert_user_has_permission(
        user, Permissions.CONFIRM_OWN_ADVICE
    ) and Advice.objects.filter(case=case, user=user):
        return JsonResponse(
            {
                "errors": "You do not have permission to confirm your own user-level advice"
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


def check_if_final_advice_exists(case):
    if FinalAdvice.objects.filter(case=case):
        return JsonResponse(
            {"errors": "Final advice already exists for this case"},
            status=status.HTTP_400_BAD_REQUEST,
        )


def check_if_team_advice_exists(case, user):
    if TeamAdvice.objects.filter(case=case, team=user.team):
        return JsonResponse(
            {"errors": "Team advice from your team already exists for this case"},
            status=status.HTTP_400_BAD_REQUEST,
        )


def check_refusal_errors(advice):
    if advice["type"].lower() == "refuse" and not advice["text"]:
        return {
            "text": [
                ErrorDetail(
                    string=get_string("cases.advice_refusal_error"), code="blank"
                )
            ]
        }
    return None


def post_advice(request, case, serializer_object, team=False):
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
