from django.db import migrations


def add_case_status_superseded_by_amendment(apps, schema_editor):
    CaseStatus = apps.get_model("statuses", "CaseStatus")

    STATUS__SUPERSEDED_BY_AMENDMENT = "00000000-0000-0000-0000-000000000034"

    CaseStatus.objects.create(
        id=STATUS__SUPERSEDED_BY_AMENDMENT,
        status="superseded_by_amendment",
        priority=34,
        is_read_only=True,
        is_terminal=True,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("statuses", "0012_add_draft_rejection_sub_status"),
    ]

    operations = [
        migrations.RunPython(add_case_status_superseded_by_amendment, migrations.RunPython.noop),
    ]
