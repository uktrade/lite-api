from django.db import migrations

ADVICETYPE_F680_ID = "00000000-0000-0000-0000-000000000008"

def update_f680_letter(apps, schema_editor):
    LetterTemplates = apps.get_model("letter_templates", "LetterTemplate")

    f680_letter_template = LetterTemplates.objects.get(name="F680 letter")
    f680_letter_template.decisions.set([ADVICETYPE_F680_ID])
    f680_letter_template.save()   

class Migration(migrations.Migration):
    dependencies = [
        ("letter_templates", "0010_f680_letter_template"),
    ]

    operations = [migrations.RunPython(update_f680_letter, migrations.RunPython.noop)]
