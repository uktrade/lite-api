# Generated by Django 4.2.13 on 2024-07-03 15:48

from django.db import migrations
from api.staticdata.units.enums import Units


def change_legacy_unit_codes(apps, schema_editor):
    GoodOnApplication = apps.get_model("applications", "GoodOnApplication")

    unit_mapping = {
        "MIM": Units.MGM,
        "MCM": Units.MCG,
        "MIR": Units.MLT,
        "MCR": Units.MCL,
    }

    for good_on_application in GoodOnApplication.objects.filter(unit__in=unit_mapping.keys()):
        legacy_unit = good_on_application.unit
        good_on_application.unit = unit_mapping[legacy_unit]
        good_on_application.save()


class Migration(migrations.Migration):

    dependencies = [
        ("applications", "0082_alter_goodonapplication_unit"),
    ]

    operations = [migrations.RunPython(change_legacy_unit_codes, migrations.RunPython.noop)]