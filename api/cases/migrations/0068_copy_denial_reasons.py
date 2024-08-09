from django.db import migrations


def copy_denial_reasons(apps, schema_editor):
    Advice = apps.get_model("cases", "Advice")
    AdviceDenialReason = apps.get_model("cases", "AdviceDenialReason")

    for advice in Advice.objects.all():
        for denial_reason in advice.denial_reasons.all():
            AdviceDenialReason.objects.create(advice=advice, denial_reason=denial_reason)


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0067_advicedenialreason_advice_denial_reasons_uuid"),
        ("denial_reasons", "0007_alter_denialreason_uuid"),
    ]

    operations = [migrations.RunPython(copy_denial_reasons, reverse_code=migrations.RunPython.noop)]
