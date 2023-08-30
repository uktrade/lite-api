from django.db import migrations


def update_inform_letter_template_paragraphs(apps, schema_editor):

    PicklistItem = apps.get_model("picklists", "PicklistItem")
    INFORM_LETTERS = [
        ("Weapons of mass destruction (WMD)", "wmd.txt"),
        ("Military", "mam.txt"),
        ("Military and weapons of mass destruction (WMD)", "mwmd.txt"),
    ]
    for name, file_name in INFORM_LETTERS:
        pick_list_item = PicklistItem.objects.get(name=name)
        with open(f"lite_content/lite_api/letter_paragraphs/inform_letter_{file_name}", "r") as f:
            text = f.read()
            pick_list_item.text = text
            pick_list_item.save()


class Migration(migrations.Migration):

    dependencies = [
        ("letter_templates", "0006_inform_letter_update_military_picklist"),
    ]

    operations = [
        migrations.RunPython(update_inform_letter_template_paragraphs, migrations.RunPython.noop),
    ]
