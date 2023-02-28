from django.db import migrations, models


def set_pending_field(apps, schema_editor):
    BaseUser = apps.get_model("users", "BaseUser")
    BaseUser.objects.all().exclude(first_name="").update(pending=False)


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0003_default_govuser_queue"),
    ]

    operations = [
        migrations.AddField(
            model_name="baseuser",
            name="pending",
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(set_pending_field, migrations.RunPython.noop),
    ]
