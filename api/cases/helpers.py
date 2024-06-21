from datetime import timedelta

from api.audit_trail.enums import AuditType
from api.common.dates import is_bank_holiday, is_weekend
from api.cases.enums import CaseTypeReferenceEnum
from api.staticdata.statuses.enums import CaseStatusEnum
from api.users.models import BaseUser, GovUser, GovNotification
from api.users.enums import SystemUser


def get_assigned_to_user_case_ids(user: GovUser, queue_id=None):
    from api.cases.models import CaseAssignment

    filters = {"user": user}
    if queue_id:
        filters["queue_id"] = queue_id

    return CaseAssignment.objects.filter(**filters).values_list("case__id", flat=True)


def get_assigned_as_case_officer_case_ids(user: GovUser):
    from api.cases.models import Case

    return Case.objects.filter(case_officer=user).values_list("id", flat=True)


def get_updated_case_ids(user: GovUser):
    """
    Get the cases that have raised notifications when updated by an exporter
    """
    assigned_to_user_case_ids = get_assigned_to_user_case_ids(user)
    assigned_as_case_officer_case_ids = get_assigned_as_case_officer_case_ids(user)
    cases = assigned_to_user_case_ids.union(assigned_as_case_officer_case_ids)

    return GovNotification.objects.filter(user_id=user.pk, case__id__in=cases).values_list("case__id", flat=True)


def can_set_status(case, status):
    """
    Returns true or false depending on different case conditions
    """
    from api.compliance.models import ComplianceVisitCase
    from api.compliance.helpers import compliance_visit_case_complete

    reference_type = case.case_type.reference

    if reference_type == CaseTypeReferenceEnum.COMP_SITE and status not in CaseStatusEnum.compliance_site_statuses:
        return False
    elif reference_type == CaseTypeReferenceEnum.COMP_VISIT and status not in CaseStatusEnum.compliance_visit_statuses:
        return False

    if case.case_type.reference == CaseTypeReferenceEnum.COMP_VISIT and CaseStatusEnum.is_terminal(status):
        comp_case = ComplianceVisitCase.objects.get(id=case.id)
        if not compliance_visit_case_complete(comp_case):
            return False

    if reference_type == CaseTypeReferenceEnum.CRE and status not in [
        CaseStatusEnum.CLOSED,
        CaseStatusEnum.SUBMITTED,
        CaseStatusEnum.RESUBMITTED,
    ]:
        return False

    return True


def working_days_in_range(start_date, end_date):
    dates_in_range = [start_date + timedelta(n) for n in range((end_date - start_date).days)]
    return len([date for date in dates_in_range if (not is_bank_holiday(date) and not is_weekend(date))])


def create_system_mention(case, case_note_text, mention_user):
    """
    Create a LITE system mention e.g. exporter responded to an ECJU query
    """
    # to avoid circular import ImportError these must be imported here
    from api.cases.models import CaseNote, CaseNoteMentions
    from api.audit_trail import service as audit_trail_service

    case_note = CaseNote(text=case_note_text, case=case, user=BaseUser.objects.get(id=SystemUser.id))
    case_note.save()
    case_note_mentions = CaseNoteMentions(user=mention_user, case_note=case_note)
    case_note_mentions.save()
    audit_payload = {
        "mention_users": [f"{mention_user.full_name} ({mention_user.team.name})"],
        "additional_text": case_note_text,
    }
    audit_trail_service.create_system_user_audit(
        verb=AuditType.CREATED_CASE_NOTE_WITH_MENTIONS, action_object=case_note, target=case, payload=audit_payload
    )
