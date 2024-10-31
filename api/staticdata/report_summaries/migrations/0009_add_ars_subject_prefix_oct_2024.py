import json

from django.db import migrations

DATA_PATH = "api/staticdata/report_summaries/migrations/data/0009_add_report_summaries_oct_2024/"


def populate_report_summaries(apps, schema_editor):

    ReportSummaryPrefix = apps.get_model("report_summaries", "ReportSummaryPrefix")
    with open(f"{DATA_PATH}/report_summary_prefix.json") as json_file:
        records = json.load(json_file)
        for attributes in records:
            ReportSummaryPrefix.objects.create(**attributes)

    ReportSummarySubject = apps.get_model("report_summaries", "ReportSummarySubject")
    with open(f"{DATA_PATH}/report_summary_subject.json") as json_file:
        records = json.load(json_file)
        for attributes in records:
            ReportSummarySubject.objects.create(**attributes)


class Migration(migrations.Migration):
    dependencies = [("report_summaries", "0008_back_populate_multiple_ars_data")]

    operations = [migrations.RunPython(populate_report_summaries, migrations.RunPython.noop)]
