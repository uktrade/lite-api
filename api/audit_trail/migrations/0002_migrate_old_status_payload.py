from django.db import migrations

from api.audit_trail.enums import AuditType


def create_missing_application_audit(apps, schema_editor):
    if schema_editor.connection.alias != "default":
        return
    ContentType = apps.get_model("contenttypes", "ContentType")
    Case = apps.get_model("cases", "Case")
    Audit = apps.get_model("audit_trail", "Audit")

    for case in Case.objects.all():
        print("Running for case {id}".format(id=case.id))
        content_type = ContentType.objects.get_for_model(case)

        activities = Audit.objects.filter(
            target_object_id=case.id, target_content_type=content_type, verb=AuditType.UPDATED_STATUS
        ).order_by("created_at")

        last_status = None
        for activity in activities:
            if "old" in activity.payload["status"]:
                # all updated for case
                break
            if last_status == None:
                # first status change assumes came from draft
                last_status = activity.payload["status"]
                activity.payload = {"status": {"old": "draft", "new": last_status}}
                activity.save()
                continue
            activity.payload = {"status": {"old": last_status, "new": activity.payload["status"]}}
            print("Updating activity: {id}".format(id=activity.id))
            activity.save()
            last_status = activity.payload["status"]["new"]


class Migration(migrations.Migration):
    dependencies = [("applications", "0022_auto_20200331_1107"), ("audit_trail", "0001_initial")]
    migrations.RunPython(create_missing_application_audit, migrations.RunPython.noop)
