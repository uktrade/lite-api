from django.db import migrations

from api.audit_trail.enums import AuditType
from api.cases.enums import CaseTypeEnum


def create_missing_create_audits(apps, schema_editor):
    if schema_editor.connection.alias != "default":
        return
    ContentType = apps.get_model("contenttypes", "ContentType")
    Case = apps.get_model("cases", "Case")
    Audit = apps.get_model("audit_trail", "Audit")

    for case in Case.objects.filter(case_type__id=CaseTypeEnum.GOODS.id):
        print("Running for goods case {id}".format(id=case.id))
        content_type = ContentType.objects.get_for_model(case)
        audits = Audit.objects.filter(verb=AuditType.UPDATED_STATUS, target_object_id=case.id).order_by("created_at")

        for audit in audits:
            if audit and audit.payload["status"]["old"] == "draft":
                print("Updating draft payload")
                audit.payload["status"]["old"] = "clc_review"
                audit.save()

        if not Audit.objects.filter(verb=AuditType.CREATED, action_object_object_id=case.id).exists():
            print("Creating original audit")
            Audit.objects.create(
                created_at=case.created_at,
                verb=AuditType.CREATED,
                action_object_object_id=case.id,
                action_object_content_type=content_type,
                payload={"status": {"new": "clc_review"}},
            )

    for case in Case.objects.filter(case_type__id=CaseTypeEnum.EUA.id):
        print("Running for eua case {id}".format(id=case.id))
        content_type = ContentType.objects.get_for_model(case)
        audits = Audit.objects.filter(verb=AuditType.UPDATED_STATUS, target_object_id=case.id).order_by("created_at")

        for audit in audits:
            if audit and audit.payload["status"]["old"] == "draft":
                print("Updating draft payload")
                audit.payload["status"]["old"] = "submitted"
                audit.save()

        if not Audit.objects.filter(verb=AuditType.CREATED, action_object_object_id=case.id).exists():
            print("Creating original audit")
            Audit.objects.create(
                created_at=case.created_at,
                verb=AuditType.CREATED,
                action_object_object_id=case.id,
                action_object_content_type=content_type,
                payload={"status": {"new": "submitted"}},
            )


class Migration(migrations.Migration):
    dependencies = [
        ("applications", "0022_auto_20200331_1107"),
        ("audit_trail", "0002_migrate_old_status_payload"),
        ("cases", "0013_auto_20200325_1544"),
    ]
    operations = [migrations.RunPython(create_missing_create_audits, migrations.RunPython.noop)]
