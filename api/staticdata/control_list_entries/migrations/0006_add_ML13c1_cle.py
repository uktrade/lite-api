from django.db import migrations


def add_cle(apps, schema_editor):
    ControlListEntry = apps.get_model("control_list_entries", "ControlListEntry")

    parent_cle = ControlListEntry.objects.get(rating="ML13c")

    ControlListEntry.objects.update_or_create(
        rating="ML13c1", text="ML13c1", parent_id=parent_cle.id, category="UK Military List", controlled=True
    )


class Migration(migrations.Migration):

    dependencies = [
        ("control_list_entries", "0005_adds_5D001e"),
    ]

    operations = [
        migrations.RunPython(add_cle, migrations.RunPython.noop),
    ]
