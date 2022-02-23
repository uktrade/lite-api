from django.db import migrations


def add_nir(apps, schema_editor):
    Country = apps.get_model("countries", "Country")
    country = Country.objects.filter(name__iexact="Northern Ireland")

    if country.exists():
        return

    Country.objects.create(id="GB-NIR", name="Northern Ireland", type="gov.uk Country", is_eu=True)


def remove_nir(apps, schema_editor):
    Country = apps.get_model("countries", "Country")
    Country.objects.filter(name__iexact="Northern Ireland").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("countries", "0002_rename_countries"),
    ]

    operations = [
        migrations.RunPython(add_nir, remove_nir),
    ]
