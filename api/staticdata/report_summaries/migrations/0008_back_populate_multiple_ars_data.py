# Generated by Django 4.2.11 on 2024-05-13 10:52
import logging
from django.db import migrations

logger = logging.getLogger(__name__)


def back_populate_multiple_ars(apps, schema_editor):
    """
    Look at all the controlled Goods on application and populate their report_summaries.
    As there can be large number of entries, instead of setting on each good on application instance
    we create entries in bulk on the through table for GoodOnApplication and ReportSummary
    """
    GoodOnApplication = apps.get_model("applications", "GoodOnApplication")
    ReportSummary = apps.get_model("report_summaries", "ReportSummary")
    ReportSummaryThrough = GoodOnApplication.report_summaries.through

    # All controlled goods where report_summaries are not populated yet
    queryset_values = GoodOnApplication.objects.filter(
        is_good_controlled=True,
        report_summary_subject__isnull=False,
        report_summaries__isnull=True,
    ).values_list("id", "report_summary_prefix_id", "report_summary_subject_id")

    all_report_summaries = ReportSummary.objects.values_list("id", "prefix", "subject")
    all_report_summary_cache = {f"{prefix}-{subject}": f"{id}" for id, prefix, subject in all_report_summaries}

    errors = []
    valid_report_summaries = []
    for goodonapplication_id, prefix_id, subject_id in queryset_values:
        report_summary_key = f"{prefix_id}-{subject_id}"
        report_summary_id = all_report_summary_cache.get(report_summary_key, None)
        if report_summary_id:
            valid_report_summaries.append((goodonapplication_id, report_summary_id))
        else:
            errors.append({"prefix": prefix_id, "subject": subject_id})

    if errors:
        logger.info("ReportSummary objects does not exist for,\n%s", errors)

    # Create the entries in through table
    objects_to_create = [
        ReportSummaryThrough(goodonapplication_id=goodonapplication_id, reportsummary_id=report_summary_id)
        for (goodonapplication_id, report_summary_id) in valid_report_summaries
    ]

    ReportSummaryThrough.objects.bulk_create(objects_to_create)


class Migration(migrations.Migration):

    dependencies = [
        ("report_summaries", "0007_populate_report_summaries"),
    ]

    operations = [
        migrations.RunPython(back_populate_multiple_ars, migrations.RunPython.noop),
    ]
