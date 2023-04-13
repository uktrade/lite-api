from django.db import migrations, models


class Migration(migrations.Migration):
    def populate_control_list_entries(apps, schema_editor):
        ControlListEntry = apps.get_model("control_list_entries", "ControlListEntry")
        ControlListEntry.objects.get_or_create(
            rating="5D001e", text="5D001e", parent_id=None, category="Dual-Use List", controlled=True
        )

    dependencies = [
        ("control_list_entries", "0004_controllistentry_new_entries_20221130"),
    ]

    operations = [
        migrations.RunPython(populate_control_list_entries, migrations.RunPython.noop),
    ]
