from django.db import migrations


def change_inform_letter_decision_type(apps, schema_editor):

    ADVICETYPE_INFORM_ID = "00000000-0000-0000-0000-000000000007"

    LetterTemplates = apps.get_model("letter_templates", "LetterTemplate")
    letter_template = LetterTemplates.objects.get(name="Inform letter")
    letter_template.decisions.set([ADVICETYPE_INFORM_ID])


class Migration(migrations.Migration):

    dependencies = [
        ("letter_templates", "0004_inform_letter_template"),
        ("decisions", "0003_add_inform_decision"),
    ]

    operations = [
        migrations.RunPython(change_inform_letter_decision_type, migrations.RunPython.noop),
    ]
