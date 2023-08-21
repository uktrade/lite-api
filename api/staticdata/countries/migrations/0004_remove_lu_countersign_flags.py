from django.db import migrations

from lite_routing.routing_rules_internal.enums import FlagsEnum


def remove_lu_countersign_flags(apps, schema_editor):
    Flag = apps.get_model("flags", "Flag")
    Country = apps.get_model("countries", "Country")
    flags_to_remove = list(
        Flag.objects.filter(
            id__in=[
                FlagsEnum.LU_COUNTER_REQUIRED,
                FlagsEnum.LU_SENIOR_MANAGER_CHECK_REQUIRED,
            ],
        )
    )
    countries_with_countersign_flags = Country.objects.filter(flags__in=flags_to_remove)
    for country in countries_with_countersign_flags:
        country.flags.remove(*flags_to_remove)


class Migration(migrations.Migration):
    dependencies = [
        ("countries", "0003_add_nir"),
    ]

    operations = [
        migrations.RunPython(remove_lu_countersign_flags, migrations.RunPython.noop),
    ]
