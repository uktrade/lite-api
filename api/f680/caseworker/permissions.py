from rest_framework import permissions

from api.staticdata.statuses.enums import CaseStatusEnum

from lite_routing.routing_rules_internal.enums import TeamIdEnum

OGDS_FOR_F680 = (
    TeamIdEnum.MOD_CAPPROT,
    TeamIdEnum.MOD_DSR,
    TeamIdEnum.MOD_DI,
    TeamIdEnum.NCSC,
    TeamIdEnum.MOD_DSTL,
    TeamIdEnum.FCDO,
)


class ReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method == "GET"


class CaseCanAcceptRecommendations(permissions.BasePermission):
    def has_permission(self, request, view):
        return view.get_case().status.status == CaseStatusEnum.OGD_ADVICE


class CaseCanUserMakeRecommendations(permissions.BasePermission):
    def has_permission(self, request, view):
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
        return view.get_case().status.status == CaseStatusEnum.UNDER_FINAL_REVIEW


class CanUserMakeOutcome(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return str(user.govuser.team.id) == TeamIdEnum.MOD_ECJU
