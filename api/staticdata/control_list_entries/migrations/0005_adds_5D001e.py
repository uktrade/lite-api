from django.db import migrations


class Migration(migrations.Migration):
    def populate_control_list_entries(apps, schema_editor):
        ControlListEntry = apps.get_model("control_list_entries", "ControlListEntry")

        great_grandparent_cle, _ = ControlListEntry.objects.update_or_create(
            id="ce17c22f-cc8c-4fa5-af3a-92c5310a9a46",
            rating="5",
            parent_id=None,
            category="Dual-Use List",
            controlled=True,
            defaults={"text": "Telecommunications and Information Security"},
        )
        grandparent_cle, _ = ControlListEntry.objects.update_or_create(
            id="addb336b-4ef2-4515-b1ea-493f11f95b03",
            rating="5P1",
            text="Telecommunications",
            parent_id=great_grandparent_cle.id,
            category="Dual-Use List",
            controlled=True,
        )
        parent_cle, _ = ControlListEntry.objects.update_or_create(
            id="f7ecac05-ef4c-4724-a89f-0972d449bc63",
            rating="5D1",
            parent_id=grandparent_cle.id,
            category="Dual-Use List",
            controlled=True,
            defaults={"text": "Software"},
        )

        ControlListEntry.objects.update_or_create(
            rating="5D001e", text="5D001e", parent_id=parent_cle.id, category="Dual-Use List", controlled=True
        )

    dependencies = [
        ("control_list_entries", "0004_controllistentry_new_entries_20221130"),
    ]

    operations = [
        migrations.RunPython(populate_control_list_entries, migrations.RunPython.noop),
    ]
