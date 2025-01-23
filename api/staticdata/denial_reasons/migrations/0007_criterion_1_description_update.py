from django.db import migrations


def update_denial_reason(apps, schema_editor):
    DenialReason = apps.get_model("denial_reasons", "DenialReason")
    denial_reason = DenialReason.objects.get(id=1)
    if denial_reason:
        denial_reason.description = "Respect for the UK's international obligations and commitments, in particular sanctions adopted by the UN Security Council, agreements on non-proliferation and other subjects, as well as other international obligations."
        denial_reason.save()


class Migration(migrations.Migration):
    dependencies = [
        ("denial_reasons", "0006_populate_uuid_field"),
    ]

    operations = [
        migrations.RunPython(update_denial_reason, migrations.RunPython.noop),
    ]
