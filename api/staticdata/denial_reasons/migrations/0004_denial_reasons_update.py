from django.db import migrations
import csv


def update_denial_reasons(apps, schema_editor):
    DenialReason = apps.get_model("denial_reasons", "DenialReason")
    with open("lite_content/lite_api/denial_reasons_update.csv", "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            DenialReason.objects.update_or_create(
                id=row["id"],
                defaults={
                    "display_value": row["display_value"],
                    "deprecated": row["deprecated"],
                    "description": row["description"],
                },
            )


class Migration(migrations.Migration):
    dependencies = [
        ("denial_reasons", "0003_criterion_1_to_false"),
    ]

    operations = [
        migrations.RunPython(update_denial_reasons, migrations.RunPython.noop),
    ]
