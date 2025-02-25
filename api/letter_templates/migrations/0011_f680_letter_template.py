from django.db import migrations


def populate_f680_letter_template(apps, schema_editor):

    CASETYPE_F680_ID = "00000000-0000-0000-0000-000000000007"

    LetterLayout = apps.get_model("letter_layouts", "LetterLayout")
    LetterTemplates = apps.get_model("letter_templates", "LetterTemplate")

    # Create the template and layout
    f680_approval_layout = LetterLayout.objects.get_or_create(name="F680 Approval", filename="f680_approval")

    f680_approval_template = LetterTemplates.objects.get_or_create(
        name="F680 Approval", layout=f680_approval_layout, visible_to_exporter=True, include_digital_signature=True
    )

    f680_approval_template.case_types.set([CASETYPE_F680_ID])
    f680_approval_template.save()


class Migration(migrations.Migration):

    dependencies = [
        ("letter_templates", "0010_refusal_letter_picklist_update_team_ownership"),
    ]

    operations = [
        migrations.RunPython(populate_f680_letter_template, migrations.RunPython.noop),
    ]
