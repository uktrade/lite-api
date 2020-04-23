from django.db import migrations

from audit_trail.schema import AuditType


def fill_in_missing_actor(apps, schema_editor):
    if schema_editor.connection.alias != "default":
        return
    ContentType = apps.get_model("contenttypes", "ContentType")
    Audit = apps.get_model("audit_trail", "Audit")
    ExporterUser = apps.get_model("users", "ExporterUser")
    content_type = ContentType.objects.get_for_model(ExporterUser)
    print("Filling in missing actors")
    for audit in Audit.objects.filter(
        actor_content_type__isnull=True,
        verb__in=[AuditType.UPDATED_STATUS.value, AuditType.CREATED.value]
    ):
        print("Updating audit for:", audit.id)
        audit.actor_content_type = content_type
        audit.actor_object_id = ExporterUser.objects.first().id
        audit.save()


class Migration(migrations.Migration):
    dependencies = [
        ("applications", "0022_auto_20200331_1107"),
        ("audit_trail", "0004_case_submitted_audits"),
    ]
    operations = [
        migrations.RunPython(fill_in_missing_actor),
    ]
