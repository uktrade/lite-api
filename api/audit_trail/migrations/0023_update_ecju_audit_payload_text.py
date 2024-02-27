import logging
from django.db import migrations, transaction
from django.db.models import Q

from api.audit_trail.enums import AuditType


logger = logging.getLogger(__name__)


def update_ecju_audit_payload_text(apps, schema_editor):
    Audit = apps.get_model("audit_trail", "Audit")
    with transaction.atomic():
        # Audit ECJU used some old style formatting
        # Since we have change the string variables we need to 
        # change the text to additional_text for the N&T generic display pattern

        old_format_ecju_response_events = Audit.objects.filter(
            Q(verb=AuditType.ECJU_QUERY_RESPONSE) |
             Q(verb=AuditType.ECJU_QUERY_MANUALLY_CLOSED) 
        )

        for ecju_audit_response in old_format_ecju_response_events:
            ecju_response_payload =  ecju_audit_response.payload
            if ecju_response_payload.get("ecju_response"):
                ecju_audit_response.payload["additional_text"] = ecju_response_payload.pop("ecju_response")
                ecju_audit_response.save()

                logger.info("Updating payload from ecju_response to additional_text on audit object %s", ecju_audit_response.id)

        ecju_query_audit_objects = Audit.objects.filter(verb=AuditType.ECJU_QUERY)

        for ecju_query_audit in ecju_query_audit_objects:
            ecju_query_audit_payload =  ecju_query_audit.payload
            if ecju_query_audit_payload.get("ecju_query"):
                ecju_query_audit.payload["additional_text"] = ecju_query_audit_payload.pop("ecju_query")
                ecju_query_audit.save()
                logger.info("Updating payload from ecju_audit to additional_text on audit object %s", ecju_query_audit.id)


class Migration(migrations.Migration):

    dependencies = [
        ("audit_trail", "0022_alter_audit_verb"),
    ]

    operations = [migrations.RunPython(update_ecju_audit_payload_text, migrations.RunPython.noop)]
