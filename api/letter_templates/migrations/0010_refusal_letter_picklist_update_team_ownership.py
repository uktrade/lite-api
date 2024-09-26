from django.db import migrations

LICENSING_UNIT_TEAM_ID = "58e77e47-42c8-499f-a58d-94f94541f8c6"


def refusal_letter_picklist_update_team_ownership(apps, schema_editor):

    PicklistItem = apps.get_model("picklists", "PicklistItem")
    refusal_letter_content = PicklistItem.objects.get(name="Refusal letter content")
    refusal_letter_content.team_id = LICENSING_UNIT_TEAM_ID
    refusal_letter_content.save()


class Migration(migrations.Migration):

    dependencies = [
        ("letter_templates", "0009_refusal_letter_update_fix"),
    ]

    operations = [
        migrations.RunPython(refusal_letter_picklist_update_team_ownership, migrations.RunPython.noop),
    ]
