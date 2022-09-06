from django.conf import settings
from django.db.models.signals import pre_save
from django.dispatch import receiver

from api.cases.models import Case
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from api.workflow.flagging_rules_automation import apply_flagging_rules_to_case


@receiver(pre_save, sender=Case)
def case_pre_save_handler(sender, instance, raw=False, **kwargs):
    if not settings.FEATURE_C5_ROUTING_ENABLED:
        return

    if raw:
        return

    if not instance.id:
        return

    original = None
    try:
        original = Case.objects.get(pk=instance.id)
    except Case.DoesNotExist:
        return

    status_changed = original.status != instance.status
    status_draft = instance.status == get_case_status_by_status(CaseStatusEnum.DRAFT)
    new_status_terminal = instance.status.is_terminal
    if status_changed and not status_draft and not new_status_terminal:
        apply_flagging_rules_to_case(instance)
