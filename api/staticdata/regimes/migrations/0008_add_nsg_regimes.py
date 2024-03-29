# Generated by Django 3.2.15 on 2022-12-02 17:00
import csv
import os

from django.db import migrations, transaction

from api.staticdata.regimes.enums import RegimesEnum, RegimeSubsectionsEnum


def create_entries(RegimeEntry, subsection, entries_csv_filename):
    data_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(data_path, "data", entries_csv_filename)
    with open(file_path) as csvfile:
        reader = csv.reader(csvfile)
        for name, *_ in reader:
            RegimeEntry.objects.create(
                subsection=subsection,
                name=name,
            )


def create_nsg_regimes(apps, schema_editor):
    Regime = apps.get_model("regimes", "Regime")
    RegimeSubsection = apps.get_model("regimes", "RegimeSubsection")
    RegimeEntry = apps.get_model("regimes", "RegimeEntry")

    with transaction.atomic():
        nsg_regime = Regime.objects.create(
            id=RegimesEnum.NSG,
            name="NSG",
        )

        nsg_potential_trigger_list_subsection = RegimeSubsection.objects.create(
            id=RegimeSubsectionsEnum.NSG_POTENTIAL_TRIGGER_LIST,
            name="NSG Potential Trigger List",
            regime=nsg_regime,
        )
        create_entries(
            RegimeEntry,
            nsg_potential_trigger_list_subsection,
            "NSG_Potential_trigger_list.csv",
        )

        nsg_dual_use_subsection = RegimeSubsection.objects.create(
            id=RegimeSubsectionsEnum.NSG_POTENTIAL_DUAL_USE,
            name="NSG Dual-Use",
            regime=nsg_regime,
        )
        create_entries(
            RegimeEntry,
            nsg_dual_use_subsection,
            "NSG_Dual_use.csv",
        )


class Migration(migrations.Migration):

    dependencies = [
        ("regimes", "0007_add_ag_regimes"),
    ]

    operations = [
        migrations.RunPython(
            create_nsg_regimes,
            migrations.RunPython.noop,
        ),
    ]
