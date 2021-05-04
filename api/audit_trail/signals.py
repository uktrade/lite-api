import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from api.audit_trail.models import Audit
from api.audit_trail.serializers import AuditSerializer


logger = logging.getLogger(__name__)


@receiver(post_save, sender=Audit)
def emit_audit_log(sender, instance, **kwargs):
    """Emit log entry when an Audit instance is saved to the DB.
    """
    text = str(instance)
    extra = AuditSerializer(instance).data
    logger.info(text, extra={"audit": extra})
