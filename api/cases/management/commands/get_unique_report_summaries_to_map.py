import re

from django.core.management.base import BaseCommand, CommandError

from api.cases.models import Case
from api.applications.models import GoodOnApplication


class Command(BaseCommand):
    help = "Get a list of unique legacy report summary strings to map."

    def handle(self, *args, **options):
        goas_missing_report_summary_subject = GoodOnApplication.objects.filter(
            report_summary_subject=None, report_summary__isnull=False, is_good_controlled=True
        )

        unique_report_summaries = set()

        for goa in goas_missing_report_summary_subject:
            unique_report_summaries.add(re.sub("\(\d+\)", "", goa.report_summary).strip().lower())

        self.stdout.write("Unique report summaries to map")
        for rs in unique_report_summaries:
            self.stdout.write(rs)

        self.stdout.write("*********")

        self.stdout.write(
            f"Total GoodOnApplications missing report summary subject (which have legacy report_summary): {goas_missing_report_summary_subject.count()}"
        )
        self.stdout.write(f"Unique report summaries to map: {len(unique_report_summaries)}")

        goas_missing_any_report_summary = GoodOnApplication.objects.filter(
            report_summary=None, report_summary_subject=None, is_good_controlled=True
        )
        self.stdout.write(
            f"Total GoodOnApplications missing report summary subject (which have no report_summary): {goas_missing_any_report_summary.count()}"
        )

        goas_non_controlled_with_report_summary = GoodOnApplication.objects.filter(
            report_summary__isnull=False,
            is_good_controlled=False,
        )
        self.stdout.write(
            f"Total GoodOnApplications with a report summary which should be None: {goas_non_controlled_with_report_summary.count()}"
        )
