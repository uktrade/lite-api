from datetime import timedelta

from api.audit_trail.enums import AuditType
from api.common.dates import is_bank_holiday, is_weekend
from api.users.models import BaseUser, GovUser
from api.users.enums import SystemUser
from api.staticdata.statuses.enums import CaseStatusEnum
from api.cases.enums import ApplicationFeatures


def get_assigned_to_user_case_ids(user: GovUser, queue_id=None):
    from api.cases.models import CaseAssignment

    filters = {"user": user}
    if queue_id:
        filters["queue_id"] = queue_id

    return CaseAssignment.objects.filter(**filters).values_list("case__id", flat=True)


def get_assigned_as_case_officer_case_ids(user: GovUser):
    from api.cases.models import Case

    return Case.objects.filter(case_officer=user).values_list("id", flat=True)


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


def is_case_already_finalised(case):
    from api.cases.models import Case
    from api.licences.models import Licence

    # To handle a user double clicking when a request takes a while to respond
    # Retrieve the case from db and lock the row to check its status
    original_case = Case.objects.select_for_update().get(pk=case.pk)
    original_case.refresh_from_db()

    # Not finalised so return False and None (no licence)
    if original_case.status.status != CaseStatusEnum.FINALISED:
        return False, None

    # If a licence does not need to be issued for this application type then exit
    application_manifest = case.get_application_manifest()
    if not application_manifest.has_feature(ApplicationFeatures.LICENCE_ISSUE):
        return True, None

    # If a licence exists return it if not the application was rejected so no licence present
    try:
        licence = Licence.objects.get(case=case)
    except Licence.DoesNotExist:
        return True, None
    return True, licence
