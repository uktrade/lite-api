from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.core.constants import GovPermissions
from api.core.permissions import assert_user_has_permission
from api.staticdata.statuses.enums import CaseStatusEnum
from api.users.models import GovUser


def optional_str_to_bool(optional_string: str):
    if optional_string is None:
        return None
    elif optional_string.lower() == "true":
        return True
    elif optional_string.lower() == "false":
        return False
    else:
        raise ValueError("You provided " + optional_string + ', while the allowed values are None, "true" or "false"')


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


def create_submitted_audit(user, application, old_status: str, additional_payload=None) -> None:
    if not additional_payload:
        additional_payload = {}

    payload = {
        "status": {
            "new": CaseStatusEnum.RESUBMITTED if old_status != CaseStatusEnum.DRAFT else CaseStatusEnum.SUBMITTED,
            "old": old_status,
        },
        **additional_payload,
    }

    audit_trail_service.create(
        actor=user,
        verb=AuditType.UPDATED_STATUS,
        target=application.get_case(),
        payload=payload,
        ignore_case_status=True,
        send_notification=False,
    )
