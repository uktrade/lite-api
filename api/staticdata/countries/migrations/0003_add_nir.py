from django.db import migrations


def add_nir(apps, schema_editor):
    Country = apps.get_model("countries", "Country")
    gb_nier = Country.objects.filter(name__iexact="Northern Ireland")

    if gb_nier.exists():
        return

    Country.objects.create(id="GB-NIR", name="Northern Ireland", type="gov.uk Country", is_eu=False)

    gb_query = Country.objects.filter(name__iexact="Great Britain")
    if gb_query.exists():
        gb = gb_query.first()
        gb.is_eu = False
        gb.save()


def remove_nir(apps, schema_editor):
    Country = apps.get_model("countries", "Country")
    Country.objects.filter(name__iexact="Northern Ireland").delete()

    gb_query = Country.objects.filter(name__iexact="Great Britain")
    if gb_query.exists():
        gb = gb_query.first()
        gb.is_eu = True
        gb.save()


class Migration(migrations.Migration):
    dependencies = [
        ("countries", "0002_rename_countries"),
    ]

    operations = [
        migrations.RunPython(add_nir, remove_nir),
    ]
