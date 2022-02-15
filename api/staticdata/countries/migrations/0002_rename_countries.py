from django.db import migrations

from api.staticdata.countries.models import Country


def rename_countries(apps, schema_editor):
    change_needed = {"United Kingdom": "Great Britain", "St Vincent": "St Vincent and the Grenadines"}

    for key in change_needed:
        country_query = Country.objects.filter(name__iexact=key)

        if country_query.exists():
            country = country_query.first()
            country.name = change_needed[key]
            country.save()


def rename_reverse_countries(apps, schema_editor):
    change_needed = {"Great Britain": "United Kingdom", "St Vincent and the Grenadines": "St Vincent"}

    for key in change_needed:
        country_query = Country.objects.filter(name__iexact=key)

        if country_query.exists():
            country = country_query.first()
            country.name = change_needed[key]
            country.save()


class Migration(migrations.Migration):
    dependencies = [
        ("countries", "0001_squashed_0003_auto_20210105_1058"),
    ]

    operations = [
        migrations.RunPython(rename_countries, rename_reverse_countries),
    ]
