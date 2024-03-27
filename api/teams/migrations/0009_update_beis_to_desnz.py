from django.db import migrations


def update_beis_to_desnz(apps, schema_editor):
    Department = apps.get_model("teams", "Department")
    desnz = Department.objects.filter(name="BEIS")
    if desnz.exists():
        desnz.update(name="DESNZ")


class Migration(migrations.Migration):

    dependencies = [
        ("teams", "007_rename_fco"),
    ]

    operations = [migrations.RunPython(update_beis_to_desnz, migrations.RunPython.noop)]
