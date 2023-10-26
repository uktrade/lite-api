from django.db.models import F, Func, Value, ExpressionWrapper
from django.db.models.functions import Lower
from django.db.models.fields import TextField
from django.db.models.query import QuerySet

from django.core.management.base import BaseCommand

from typing import Dict

import xlsxwriter

from api.applications.models import GoodOnApplication


def annotate_with_normalised_summary(q):
    # TODO - move this onto queryset
    return q.annotate(
        # Remove any numeric suffix from the report summary, also the literal string r"(x)"
        normalised_report_summary=Lower(
            ExpressionWrapper(
                Func(F("report_summary"), Value(r"\s\(\d+\)$|\s\(x\)$"), Value(""), function="REGEXP_REPLACE"),
                output_field=TextField(),
            ),
        ),
    )


class Command(BaseCommand):
    worksheet_headers = "id name report_summary report_summary_prefix report_summary_subject".split()

    def _output_worksheet_headers(self, worksheet, row_no):
        for col_no, header in enumerate(self.worksheet_headers):
            worksheet.write(row_no, col_no, header)

    def _output_mappings_worksheet_row(self, worksheet, row_no, good_on_application, example_good_on_application):

        report_summary_subject = getattr(example_good_on_application.report_summary_subject, "name", None) or ""
        report_summary_prefix = getattr(example_good_on_application.report_summary_prefix, "name", None) or ""
        data = {
            "id": str(good_on_application.pk),
            "name": good_on_application.name,
            "report_summary": good_on_application.normalised_report_summary or good_on_application.report_summary,
            "report_summary_prefix": report_summary_prefix,
            "report_summary_subject": report_summary_subject,
        }

        for col_no, header in enumerate(self.worksheet_headers):
            worksheet.write(row_no, col_no, data[header])

    def _get_mapped_good_on_applications(
        self, unpopulated_good_on_applications: QuerySet, example_good_on_applications: Dict[str, GoodOnApplication]
    ):
        for good_on_application in unpopulated_good_on_applications:
            example_good_on_application = example_good_on_applications.get(
                good_on_application.normalised_report_summary
            )
            if example_good_on_application:
                yield good_on_application, example_good_on_application

    def output_mappings_worksheet(
        self, worksheet, unpopulated_good_on_applications, populated_good_on_applications, example_good_on_applications
    ):
        start_row = 3
        self._output_worksheet_headers(worksheet, start_row)

        matches = 0
        for row_no, (unpopulated_good_on_application, populated_good_on_application) in enumerate(
            self._get_mapped_good_on_applications(unpopulated_good_on_applications, example_good_on_applications),
            start=start_row + 1,
        ):
            self._output_mappings_worksheet_row(
                worksheet, row_no, unpopulated_good_on_application, populated_good_on_application
            )
            matches += 1

        worksheet.write(1, 0, f"{matches} GoodOnApplications.")

    def output_report_summary_fields(self, worksheet, good_on_applications, unmapped_report_summaries):
        start_row = 3

        data = set()
        for good_on_application in good_on_applications:
            report_summary_prefix = getattr(good_on_application.report_summary_prefix, "name", "-") or ""
            report_summary_subject = getattr(good_on_application.report_summary_subject, "name", "-") or ""
            data.add((good_on_application.normalised_report_summary, report_summary_prefix, report_summary_subject))

        worksheet.write(start_row, 1, "report_summary")
        worksheet.write(start_row, 2, "prefix")
        worksheet.write(start_row, 3, "subject")
        for row_no, (normalised_report_summary, report_prefix, report_summary_subject) in enumerate(
            sorted(data, key=lambda item: item[0]), start=start_row + 1
        ):
            if normalised_report_summary in unmapped_report_summaries:
                worksheet.write(row_no, 0, "UNMAPPED")
            worksheet.write(row_no, 1, normalised_report_summary)
            worksheet.write(row_no, 2, report_prefix)
            worksheet.write(row_no, 3, report_summary_subject)

    def handle(self, *args, **kwargs):
        """
        Output a workbook with three sheets:

        match_report_summary:  This sheet has items where the report summary matches existing items.
        match_report_subject:  This is items that did not match in the first sheet, but have a matching subject.
        unmatched:  This is items that do not match in either sheet.
        """
        workbook = xlsxwriter.Workbook("data-to-normalise.xlsx")

        good_on_applications = annotate_with_normalised_summary(
            GoodOnApplication.objects.exclude(report_summary__isnull=True).order_by("report_summary")
        )

        unpopulated_good_on_applications = good_on_applications.filter(
            report_summary_prefix__isnull=True, report_summary_subject__isnull=True
        ).all()

        populated_good_on_applications = good_on_applications.exclude(pk__in=unpopulated_good_on_applications).all()

        # Candidate good_on_application instance mapped by normalised_report_summary
        # Each of the mappings worksheets only contains good_on_applications in a given mapping.
        has_prefix_and_subject = {}
        has_subject = {}
        mapped_report_summaries = set()
        for good_on_application in populated_good_on_applications:
            if good_on_application.report_summary_subject:
                if good_on_application.report_summary_prefix:
                    has_prefix_and_subject[good_on_application.report_summary] = good_on_application
                else:
                    has_subject[good_on_application.report_summary] = good_on_application
                mapped_report_summaries.add(good_on_application.report_summary)

        unmapped_report_summaries = {
            good_on_application.normalised_report_summary: good_on_application
            for good_on_application in unpopulated_good_on_applications
            if good_on_application.report_summary not in mapped_report_summaries
        }

        worksheet_match_both = workbook.add_worksheet("Matched Prefixed reports")
        worksheet_match_both.write(
            0, 0, "Match on existing GoodOnApplication prefix and subject that match the report_summary."
        )

        worksheet_match_subject = workbook.add_worksheet("Matched Unprefixed reports")
        worksheet_match_subject.write(
            0, 0, "Match on existing GoodOnApplication with only a subject that match the report_summary."
        )

        worksheet_unmatched = workbook.add_worksheet("Unmatched")
        worksheet_unmatched.write(0, 0, "Items here could not be matched to an existing GoodOnApplication")

        self.output_mappings_worksheet(
            worksheet_match_both,
            unpopulated_good_on_applications,
            populated_good_on_applications,
            has_prefix_and_subject,
        )
        self.output_mappings_worksheet(
            worksheet_match_subject, unpopulated_good_on_applications, populated_good_on_applications, has_subject
        )
        self.output_mappings_worksheet(
            worksheet_unmatched,
            unpopulated_good_on_applications,
            populated_good_on_applications,
            unmapped_report_summaries,
        )

        worksheet_supplementary = workbook.add_worksheet("Prefix Subject Mappings")
        worksheet_supplementary.write(0, 0, "Report summaries and associated prefix and subjects")
        worksheet_supplementary.write(1, 0, f"{len(unmapped_report_summaries)} unmapped")
        self.output_report_summary_fields(worksheet_supplementary, good_on_applications, unmapped_report_summaries)
        workbook.close()

        self.stdout.write(self.style.SUCCESS(f"Saved data to: {workbook.filename}"))
