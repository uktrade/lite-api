from django.db import migrations

from api.audit_trail.enums import AuditType


def update_granted_application_payload_type(apps, schema_editor):
    """
    Convert old AuditType.verb with format to new AuditType.verb as enum value.
    """
    if schema_editor.connection.alias != "default":
        return

    Audit = apps.get_model("audit_trail", "Audit")
    Licence = apps.get_model("licences", "Licence")

    for audit in Audit.objects.filter(verb=AuditType.GRANTED_APPLICATION):
        if "start_date" not in audit.payload:
            print("Updating GRANTED_APPLICATION audit payload:", audit.id)
            try:
                start_date = Licence.objects.get(application__id=audit.target_object_id).start_date
            except Licence.DoesNotExist:
                start_date = audit.created_at

            audit.payload["start_date"] = start_date.date().strftime("%Y-%m-%d")
            audit.save()


class Migration(migrations.Migration):
    dependencies = [
        ("audit_trail", "0007_migrate_audit_verbs"),
        ("licences", "0002_licence_decisions"),
    ]
    operations = [migrations.RunPython(update_granted_application_payload_type, migrations.RunPython.noop)]
