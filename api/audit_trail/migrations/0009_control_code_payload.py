from django.db import migrations

from api.audit_trail.enums import AuditType


def update_good_review_payload(apps, schema_editor):
    """
    Convert old AuditType.verb with format to new AuditType.verb as enum value.
    """
    if schema_editor.connection.alias != "default":
        return

    Audit = apps.get_model("audit_trail", "Audit")
    count = 0

    for audit in Audit.objects.filter(verb=AuditType.GOOD_REVIEWED):
        if "new_control_code" in audit.payload:
            print("UPDAING FOR", audit.id)
            new_payload = {
                "good_name": audit.payload["good_name"],
                "old_control_list_entry": audit.payload["old_control_code"],
                "new_control_list_entry": audit.payload["new_control_code"],
            }
            audit.payload = new_payload
            count += 1
            audit.save()

    if count:
        print({"updated": count, "existing": Audit.objects.filter(verb=AuditType.GOOD_REVIEWED).count()})


class Migration(migrations.Migration):
    dependencies = [
        ("audit_trail", "0008_granted_application_backfill"),
    ]
    operations = [migrations.RunPython(update_good_review_payload, migrations.RunPython.noop)]
