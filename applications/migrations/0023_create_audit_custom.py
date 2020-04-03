from django.db import migrations

from audit_trail.schema import AuditType
from static.statuses.enums import CaseStatusEnum


def create_missing_application_audit(apps, schema_editor):
    if schema_editor.connection.alias != "default":
        return

    ContentType = apps.get_model("contenttypes", "ContentType")
    Case = apps.get_model("cases", "Case")
    Audit = apps.get_model("audit_trail", "Audit")
    case_qs = Case.objects.filter(status__status=CaseStatusEnum.DRAFT).values("id", "created_at")

    case_content_type = ContentType.objects.get_for_model(Case)
    for case in case_qs:
        print(case)
        Audit.objects.create(
            action_object_content_type=case_content_type,
            action_object_object_id=case["id"],
            created_at=case["submitted_at"],
            verb=AuditType.CREATED.value,
        )


class Migration(migrations.Migration):

    dependencies = [("applications", "0022_auto_20200331_1107"), ("audit_trail", "0001_initial")]

    operations = [
        migrations.RunPython(create_missing_application_audit),
    ]
