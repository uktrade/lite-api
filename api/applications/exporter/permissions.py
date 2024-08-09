from rest_framework import permissions

from api.staticdata.statuses.enums import CaseStatusEnum


# TODO: Review where django-rules can help simplify this
class CaseStatusExporterChangeable(permissions.BasePermission):
    def has_object_permission(self, request, view, application):
        new_status = request.data.get("status")
        original_status = application.status.status

        if new_status == CaseStatusEnum.WITHDRAWN and not CaseStatusEnum.is_terminal(original_status):
            return True

        if new_status == CaseStatusEnum.SURRENDERED and original_status == CaseStatusEnum.FINALISED:
            return True

        if new_status == CaseStatusEnum.APPLICANT_EDITING and CaseStatusEnum.can_invoke_major_edit(original_status):
            return True

        return False
