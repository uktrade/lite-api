from django.db import migrations


def add_case_sub_status_draft_rejection(apps, schema_editor):
    CaseStatus = apps.get_model("statuses", "CaseStatus")
    CaseSubStatus = apps.get_model("statuses", "CaseSubStatus")

    SUB_STATUS__UNDER_APPEAL__DRAFT_REJECTION_LETTER = "00000000-0000-0000-0000-000000000012"
    CASE_STATUS_UNDER_APPEAL = CaseStatus.objects.get(status="under_appeal").id

    CaseSubStatus.objects.create(
        id=SUB_STATUS__UNDER_APPEAL__DRAFT_REJECTION_LETTER,
        name="Draft rejection letter",
        parent_status_id=CASE_STATUS_UNDER_APPEAL,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("statuses", "0009_update_request_received_name"),
        ("lite_routing", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(add_case_sub_status_draft_rejection, migrations.RunPython.noop),
    ]
