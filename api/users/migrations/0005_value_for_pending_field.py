from django.db import migrations, models


def pending_field_value(apps, schema_editor):
    BaseUser = apps.get_model("users", "BaseUser")
    BaseUser.objects.all().exclude(first_name="").update(pending=False)


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0004_baseuser_pending"),
    ]

    operations = [
        migrations.RunPython(pending_field_value, migrations.RunPython.noop),
    ]
