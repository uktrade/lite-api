from rest_framework import permissions

from api.staticdata.statuses.enums import CaseStatusEnum


class IsApplicationEditable(permissions.BasePermission):
    def has_permission(self, request, view):
        application = view.application
        return application.status.status in CaseStatusEnum.major_editable_statuses()
