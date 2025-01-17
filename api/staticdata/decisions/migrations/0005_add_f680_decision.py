from django.db import migrations


def add_f680_decision(apps, schema_editor):

    ADVICETYPE_INFORM_ID = "00000000-0000-0000-0000-000000000008"

    Decision = apps.get_model("decisions", "Decision")

    Decision.objects.get_or_create(id=ADVICETYPE_INFORM_ID, name="f680")


class Migration(migrations.Migration):

    dependencies = [
        ("decisions", "0004_alter_decision_name"),
    ]

    operations = [
        migrations.RunPython(add_f680_decision, migrations.RunPython.noop),
    ]
