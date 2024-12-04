import json

from django.db import migrations

DATA_PATH = "api/staticdata/report_summaries/migrations/data/0010_add_ars_prefix_dec_2024/"


def populate_report_summaries(apps, schema_editor):

    ReportSummaryPrefix = apps.get_model("report_summaries", "ReportSummaryPrefix")
    with open(f"{DATA_PATH}/report_summary_prefix.json") as json_file:
        records = json.load(json_file)
        for attributes in records:
            ReportSummaryPrefix.objects.create(**attributes)


class Migration(migrations.Migration):
    dependencies = [("report_summaries", "0009_add_ars_subject_prefix_oct_2024")]
    operations = [migrations.RunPython(populate_report_summaries, migrations.RunPython.noop)]
