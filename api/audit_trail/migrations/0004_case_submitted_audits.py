from django.db import migrations

from api.audit_trail.enums import AuditType
from cases.enums import CaseTypeEnum


def create_missing_case_create_audits(apps, schema_editor):
    if schema_editor.connection.alias != "default":
        return
    ContentType = apps.get_model("contenttypes", "ContentType")
    Case = apps.get_model("cases", "Case")
    Audit = apps.get_model("audit_trail", "Audit")

    for case in Case.objects.exclude(case_type_id__in=[CaseTypeEnum.GOODS.id, CaseTypeEnum.EUA.id]).order_by(
        "created_at"
    ):
        print("Running for audit update for case {id}".format(id=case.id))
        content_type = ContentType.objects.get_for_model(case)
        audits = Audit.objects.filter(verb=AuditType.UPDATED_STATUS, target_object_id=case.id).order_by("created_at")

        first_audit = audits.first()
        if first_audit and (
            first_audit.payload["status"]["old"] == "draft" and first_audit.payload["status"]["new"] != "submitted"
        ):
            print(first_audit.payload)

            first_audit.payload["status"]["old"] = "submitted"
            first_audit.save()

            Audit.objects.create(
                created_at=case.created_at,
                verb=AuditType.UPDATED_STATUS,
                target_object_id=case.id,
                target_content_type=content_type,
                payload={"status": {"new": "submitted", "old": "draft"}},
            )


class Migration(migrations.Migration):
    dependencies = [
        ("applications", "0022_auto_20200331_1107"),
        ("audit_trail", "0003_queries_created_audit"),
        ("cases", "0013_auto_20200325_1544"),
    ]
    operations = [
        migrations.RunPython(create_missing_case_create_audits),
    ]
