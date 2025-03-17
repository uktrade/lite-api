from rest_framework import permissions

from api.staticdata.statuses.enums import CaseStatusEnum


class CaseCanAcceptRecommendations(permissions.BasePermission):
    def has_permission(self, request, view):
        return view.get_case().status.status == CaseStatusEnum.OGD_ADVICE
