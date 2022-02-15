import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.audit_trail.serializers import AuditSerializer
from api.licences.models import Licence


logger = logging.getLogger(__name__)


@receiver(post_save, sender=Audit)
def emit_audit_log(sender, instance, **kwargs):
    """Emit log entry when an Audit instance is saved to the DB."""
    text = str(instance)
    extra = AuditSerializer(instance).data
    logger.info(text, extra={"audit": extra})


@receiver(pre_save, sender=Licence)
def audit_licence_status_change(sender, instance, **kwargs):
    """Audit a licence status change."""
    try:
        Licence.objects.get(id=instance.id, status=instance.status)
    except Licence.DoesNotExist:
        # The `pre_save` signal is called *before* the save() method is run and
        # the `instance` is for the object that is about to be saved. In this case,
        # if a `License` with the given parameters does not exist, it implies
        # a change in status.
        audit_trail_service.create_system_user_audit(
            verb=AuditType.LICENCE_UPDATED_STATUS,
            action_object=instance,
            target=instance.case.get_case(),
            payload={"licence": instance.reference_code, "status": instance.status},
        )
