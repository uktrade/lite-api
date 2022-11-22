from django.db import migrations


def synchronise_onward_exported_fields(apps, schema_editor):
    FirearmGoodDetails = apps.get_model("goods", "FirearmGoodDetails")
    GoodOnApplication = apps.get_model("applications", "GoodOnApplication")

    firearm_good_details = FirearmGoodDetails.objects.all()

    for firearm_detail in firearm_good_details:
        GoodOnApplication.objects.filter(firearm_details_id=firearm_detail.id).update(
            is_onward_exported=firearm_detail.is_onward_exported,
            is_onward_altered_processed=firearm_detail.is_onward_altered_processed,
            is_onward_altered_processed_comments=firearm_detail.is_onward_altered_processed_comments,
            is_onward_incorporated=firearm_detail.is_onward_incorporated,
            is_onward_incorporated_comments=firearm_detail.is_onward_incorporated_comments,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("goods", "0022_alter_firearmgooddetails_number_of_items"),
    ]

    operations = [
        migrations.RunPython(synchronise_onward_exported_fields, migrations.RunPython.noop),
    ]
