from rest_framework import permissions

from api.core.constants import GovPermissions
from api.staticdata.statuses.enums import CaseStatusEnum
from lite_routing.routing_rules_internal.enums import TeamIdEnum


# TODO: Review where django-rules can help simplify this
class CaseStatusCaseworkerChangeable(permissions.BasePermission):
    def has_object_permission(self, request, view, application):
        new_status = request.data.get("status")
        original_status = application.status.status
        user = request.user.govuser

        if new_status == CaseStatusEnum.FINALISED:
            application_manifest = application.get_application_manifest()

            is_managing_user = str(user.team.id) == application_manifest.managing_team_id
            if not is_managing_user:
                return False

            if application_manifest.managing_team_id == TeamIdEnum.LICENSING_UNIT and not user.has_permission(
                GovPermissions.MANAGE_LICENCE_FINAL_ADVICE
            ):
                return False
            return True

        if new_status == CaseStatusEnum.APPLICANT_EDITING:
            return False

        if new_status == CaseStatusEnum.SUPERSEDED_BY_EXPORTER_EDIT:
            return False

        if CaseStatusEnum.is_terminal(original_status) and not user.has_permission(GovPermissions.REOPEN_CLOSED_CASES):
            return False

        return True
