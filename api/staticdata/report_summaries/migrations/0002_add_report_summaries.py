# Generated by Django 3.2.15 on 2022-10-03 13:55
import csv
import os

from contextlib import contextmanager

from django.db import migrations, transaction


DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "0002_add_report_summaries")


@contextmanager
def open_csv_file(filename):
    file_path = os.path.join(DATA_PATH, f"{filename}.csv")
    with open(file_path) as cvsfile:
        reader = csv.reader(cvsfile)
        next(reader)
        yield reader


@transaction.atomic
def create_report_summaries(apps, schema_editor):
    ReportSummaryPrefix = apps.get_model("report_summaries", "ReportSummaryPrefix")
    with open_csv_file("report_summary_prefixes") as rows:
        for name, *_ in rows:
            ReportSummaryPrefix.objects.create(name=name)

    ReportSummarySubject = apps.get_model("report_summaries", "ReportSummarySubject")
    with open_csv_file("report_summary_subjects") as rows:
        for name, _, code_level, *_ in rows:
            ReportSummarySubject.objects.create(code_level=code_level, name=name)


class Migration(migrations.Migration):

    dependencies = [
        ("report_summaries", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            create_report_summaries,
            migrations.RunPython.noop,
        ),
    ]
