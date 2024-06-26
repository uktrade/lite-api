# Generated by Django 3.2.11 on 2023-08-21 15:57

from django.db import migrations


def change_inform_letter_template_advice_type(apps, schema_editor):

    ADVICETYPE_INFORM_ID = "00000000-0000-0000-0000-000000000007"

    LetterTemplates = apps.get_model("letter_templates", "LetterTemplate")

    inform_letter_layout = LetterTemplates.objects.get(name="Inform letter")

    inform_letter_layout.decisions.set([ADVICETYPE_INFORM_ID])
    inform_letter_layout.save()


class Migration(migrations.Migration):

    dependencies = [
        ("letter_templates", "0004_inform_letter_template"),
    ]

    operations = [
        migrations.RunPython(change_inform_letter_template_advice_type, migrations.RunPython.noop),
    ]
