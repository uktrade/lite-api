from rest_framework import permissions

from api.staticdata.statuses.enums import CaseStatusEnum

from lite_routing.routing_rules_internal.enums import TeamIdEnum

OGDS_FOR_F680 = (
    TeamIdEnum.MOD_CAPPROT,
    TeamIdEnum.MOD_DSR,
)


class CaseCanAcceptRecommendations(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "GET":
            return True

        return view.get_case().status.status == CaseStatusEnum.OGD_ADVICE


class CaseCanUserMakeRecommendations(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "GET":
            return True

        user = request.user
        if str(user.govuser.team.id) not in OGDS_FOR_F680:
            return False

        queryset = view.filter_queryset(view.get_queryset())
        user_recommendation = queryset.filter(user_id=user.id, team=user.govuser.team)
        if user_recommendation.exists() and request.method == "POST":
            return False

        return True


class CaseReadyForOutcome(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "GET":
            return True
        return view.get_case().status.status == CaseStatusEnum.UNDER_FINAL_REVIEW


class CanUserMakeOutcome(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "GET":
            return True

        user = request.user
        if str(user.govuser.team.id) != TeamIdEnum.MOD_ECJU:
            return False

        return True
