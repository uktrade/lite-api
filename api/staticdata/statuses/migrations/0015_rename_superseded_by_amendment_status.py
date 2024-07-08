from django.db import migrations


def rename_case_status_superseded_by_amendment(apps, schema_editor):
    CaseStatus = apps.get_model("statuses", "CaseStatus")

    STATUS__SUPERSEDED_BY_AMENDMENT = "00000000-0000-0000-0000-000000000034"

    status = CaseStatus.objects.get(
        id=STATUS__SUPERSEDED_BY_AMENDMENT,
    )
    status.status = "superseded_by_exporter_edit"
    status.save()


class Migration(migrations.Migration):
    dependencies = [
        ("statuses", "0014_remove_casestatus_is_read_only_and_more"),
    ]

    operations = [
        migrations.RunPython(rename_case_status_superseded_by_amendment, migrations.RunPython.noop),
    ]
