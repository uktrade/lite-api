from django.db import migrations

change_needed = [("United Kingdom", "Great Britain"), ("St Vincent", "St Vincent and the Grenadines")]


def rename_countries(apps, schema_editor):
    Country = apps.get_model("countries", "Country")
    for old_name, new_name in change_needed:
        country_query = Country.objects.filter(name__iexact=old_name)

        if country_query.exists():
            country = country_query.first()
            country.name = new_name
            country.save()


def rename_reverse_countries(apps, schema_editor):
    Country = apps.get_model("countries", "Country")
    for old_name, new_name in change_needed:
        country_query = Country.objects.filter(name__iexact=new_name)

        if country_query.exists():
            country = country_query.first()
            country.name = old_name
            country.save()


class Migration(migrations.Migration):
    dependencies = [
        ("countries", "0001_squashed_0003_auto_20210105_1058"),
    ]

    operations = [
        migrations.RunPython(rename_countries, rename_reverse_countries),
    ]
