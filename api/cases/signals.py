from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from api.applications.notify import notify_caseworker_countersign_return
from api.cases.models import Case
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from api.workflow.flagging_rules_automation import apply_flagging_rules_to_case


@receiver(pre_save, sender=Case)
def case_pre_save_handler(sender, instance, raw=False, **kwargs):
    try:
        previous_record = Case.objects.get(pk=instance.id)
        instance._previous_status = previous_record.status
    except Case.DoesNotExist:
        pass


@receiver(post_save, sender=Case)
def case_post_save_handler(sender, instance, raw=False, **kwargs):
    if raw:
        return

    status_changed = instance._previous_status and instance._previous_status != instance.status
    status_draft = instance.status == get_case_status_by_status(CaseStatusEnum.DRAFT)
    new_status_terminal = instance.status.is_terminal
    if status_changed and not status_draft and not new_status_terminal:
        apply_flagging_rules_to_case(instance)
        _check_for_countersign_rejection(instance)


def _check_for_countersign_rejection(case):
    # If a Case requires both countersignatures and first countersign is rejected then it doesn't go to second countersign queue
    # and it immediately goes back to finalise queue to edit the recommendation. In terms of status changes however the status still
    # progresses to second countersign status (rules etc are not triggered) and the case is progressed again to under final review status.
    if (
        case.status.status == CaseStatusEnum.UNDER_FINAL_REVIEW
        and case._previous_status.status == CaseStatusEnum.FINAL_REVIEW_SECOND_COUNTERSIGN
    ):
        # send notification to case officer as advice has been rejected by countersigner
        if case.case_officer and case.case_officer.email:
            notify_caseworker_countersign_return(case)
