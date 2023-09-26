from django.http import JsonResponse

from rest_framework import status
from rest_framework.request import Request
from rest_framework.exceptions import PermissionDenied

from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.cases.enums import CaseTypeSubTypeEnum
from api.core.constants import GovPermissions
from api.core.permissions import assert_user_has_permission
from api.staticdata.statuses.enums import CaseStatusEnum
from api.applications.models import HmrcQuery
from api.organisations.libraries.get_organisation import get_request_user_organisation_id
from api.users.models import GovUser
from lite_content.lite_api import strings
from lite_routing.routing_rules_internal.enums import TeamIdEnum


def optional_str_to_bool(optional_string: str):
    if optional_string is None:
        return None
    elif optional_string.lower() == "true":
        return True
    elif optional_string.lower() == "false":
        return False
    else:
        raise ValueError("You provided " + optional_string + ', while the allowed values are None, "true" or "false"')


def can_status_be_set_by_exporter_user(original_status: str, new_status: str) -> bool:
    """Check that a status can be set by an exporter user. Exporter users cannot withdraw an application
    that is already in a terminal state and they cannot set an application to `Applicant editing` if the
    application is read only.
    """
    if new_status == CaseStatusEnum.WITHDRAWN:
        if CaseStatusEnum.is_terminal(original_status):
            return False
    elif new_status == CaseStatusEnum.SURRENDERED:
        if original_status != CaseStatusEnum.FINALISED:
            return False
    elif CaseStatusEnum.is_read_only(original_status) or new_status != CaseStatusEnum.APPLICANT_EDITING:
        return False

    return True


def can_status_be_set_by_gov_user(user: GovUser, original_status: str, new_status: str, is_mod: bool) -> bool:
    """
    Check that a status can be set by a gov user. Gov users can not set a case's status to
    `Applicant editing`. They also cannot set a case's status to `Finalised` or open a closed case
    without additional permissions.
    """
    if new_status == CaseStatusEnum.APPLICANT_EDITING:
        return False

    elif CaseStatusEnum.is_terminal(original_status) and not assert_user_has_permission(
        user, GovPermissions.REOPEN_CLOSED_CASES
    ):
        return False

    if new_status == CaseStatusEnum.FINALISED:
        if is_mod:
            if not assert_user_has_permission(user, GovPermissions.MANAGE_CLEARANCE_FINAL_ADVICE):
                return False
        else:
            if not assert_user_has_permission(user, GovPermissions.MANAGE_LICENCE_FINAL_ADVICE):
                return False
    return True


def create_submitted_audit(request: Request, application: HmrcQuery, old_status: str) -> None:
    audit_trail_service.create(
        actor=request.user,
        verb=AuditType.UPDATED_STATUS,
        target=application.get_case(),
        payload={
            "status": {
                "new": CaseStatusEnum.RESUBMITTED if old_status != CaseStatusEnum.DRAFT else CaseStatusEnum.SUBMITTED,
                "old": old_status,
            }
        },
        ignore_case_status=True,
        send_notification=False,
    )


def check_user_can_set_status(request, application, data):
    """
    Checks whether an user (internal/exporter) can set the requested status
    Returns error response if user cannot set the status, None otherwise
    """

    if hasattr(request.user, "exporteruser"):
        if get_request_user_organisation_id(request) != application.organisation.id:
            raise PermissionDenied()

        if data["status"] == CaseStatusEnum.FINALISED:
            return JsonResponse(
                data={"errors": [strings.Applications.Generic.Finalise.Error.SET_FINALISED]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not can_status_be_set_by_exporter_user(application.status.status, data["status"]):
            return JsonResponse(
                data={"errors": [strings.Applications.Generic.Finalise.Error.EXPORTER_SET_STATUS]},
                status=status.HTTP_400_BAD_REQUEST,
            )
    elif hasattr(request.user, "govuser"):
        gov_user = request.user.govuser

        if data["status"] == CaseStatusEnum.FINALISED:
            lu_user = str(gov_user.team.id) == TeamIdEnum.LICENSING_UNIT
            if lu_user and assert_user_has_permission(gov_user, GovPermissions.MANAGE_LICENCE_FINAL_ADVICE):
                return None

            return JsonResponse(
                data={"errors": [strings.Applications.Generic.Finalise.Error.SET_FINALISED]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        is_licence_application = application.case_type.sub_type != CaseTypeSubTypeEnum.EXHIBITION
        if not can_status_be_set_by_gov_user(
            gov_user, application.status.status, data["status"], is_licence_application
        ):
            return JsonResponse(
                data={"errors": [strings.Applications.Generic.Finalise.Error.GOV_SET_STATUS]},
                status=status.HTTP_400_BAD_REQUEST,
            )
    else:
        return JsonResponse(data={"errors": ["Invalid user type"]}, status=status.HTTP_401_UNAUTHORIZED)

    return None
