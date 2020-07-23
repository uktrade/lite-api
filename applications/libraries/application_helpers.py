from audit_trail import service as audit_trail_service
from audit_trail.enums import AuditType
from conf.constants import GovPermissions
from conf.permissions import assert_user_has_permission
from static.statuses.enums import CaseStatusEnum


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
    """ Check that a status can be set by an exporter user. Exporter users cannot withdraw an application
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


def can_status_be_set_by_gov_user(user, original_status: str, new_status: str, is_mod: bool) -> bool:
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


def create_submitted_audit(request, application, old_status):
    audit_trail_service.create(
        actor=request.user,
        verb=AuditType.UPDATED_STATUS,
        target=application.get_case(),
        payload={
            "status": {
                "new": CaseStatusEnum.get_text(CaseStatusEnum.SUBMITTED),
                "old": CaseStatusEnum.get_text(old_status),
            }
        },
    )


def set_goods_type_countries(application):
    # If the user hasn't visited the optional goods to country mapping page, then no goods to country mappings will
    # have been saved before this point. So save mappings for all goods to all countries, which is the default
    if GoodsType.objects.filter(application=application, countries__isnull=True).exists():
        countries_on_application = CountryOnApplication.objects.filter(application=application).values_list(
            "country", flat=True
        )

        for goods_type in GoodsType.objects.filter(application=application, countries__isnull=True):
            goods_type.countries.set(countries_on_application)


def auto_approve_uk_continental_shelf(application):
    # Auto-Approve UK Continental Shelf if applicable
    if (
        CountryOnApplication.objects.filter(application=application, country_id="UKCS").exists()
        and not Advice.objects.filter(case_id=application.id, country_id="UKCS").exists()
    ):
        Advice.objects.create(
            case_id=application.id,
            user_id=SystemUser.id,
            type=AdviceType.APPROVE,
            level=AdviceLevel.FINAL,
            country_id="UKCS",
            text="",
        )
