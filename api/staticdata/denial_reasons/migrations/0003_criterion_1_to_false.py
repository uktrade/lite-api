from django.db import migrations, models


def update_denial_reason(apps, schema_editor):
    DenialReason = apps.get_model("denial_reasons", "DenialReason")
    denial_reason = DenialReason.objects.filter(id=1).first()
    if denial_reason:
        denial_reason.deprecated = False
        denial_reason.save()


class Migration(migrations.Migration):
    dependencies = [
        ("denial_reasons", "0002_denialreason_display_value"),
    ]

    operations = [
        migrations.RunPython(update_denial_reason, migrations.RunPython.noop),
    ]
