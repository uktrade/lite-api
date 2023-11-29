import contextlib
import csv
import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from parameterized import parameterized


from api.applications.management.commands.suggest_summaries import annotate_normalised_summary
from api.applications.models import GoodOnApplication
from api.applications.tests.factories import GoodOnApplicationFactory, StandardApplicationFactory
from api.goods.tests.factories import GoodFactory
from api.staticdata.report_summaries.models import ReportSummaryPrefix, ReportSummarySubject
from test_helpers.clients import DataTestClient

from typing import Optional, Dict, List, Tuple


class SuggestedReportSummariesAnnotationTest(DataTestClient):
    @parameterized.expand(
        [
            ("lower case", "lower case"),
            ("UPPER CASE", "upper case"),
            ("Mixed Case", "mixed case"),
            ("contains a bracketed number (1)", "contains a bracketed number"),
            ("contains a bracketed x (x)", "contains a bracketed x"),
        ],
    )
    def test_annotate_normalised_summary_annotation(self, report_summary, expected_normalised_report_summary):
        application = StandardApplicationFactory.create(organisation=self.organisation)
        good = GoodFactory.create(
            organisation=self.organisation,
        )
        good_on_application_pk = GoodOnApplicationFactory.create(
            application=application, good=good, report_summary=report_summary
        ).pk

        normalised_report_summary = (
            (annotate_normalised_summary(GoodOnApplication.objects.filter(id=good_on_application_pk)))
            .get()
            .normalised_report_summary
        )

        assert normalised_report_summary == expected_normalised_report_summary

    @parameterized.expand(
        [
            ("arts and crafts", {}, "arts and crafts"),
            ("art and craft", {"art and craft": "arts and crafts"}, "arts and crafts"),
        ],
    )
    def test_annotation_can_find_remapped_summaries(
        self, report_summary, report_summary_mappings, expected_report_summary
    ):
        """
        Verify that normalised_report_summary is remapped to the expected value if the value of report_summary
        is a key in report_summary_mappings.

        :param report_summary: The value of the report_summary field on the GoodOnApplication
        :param report_summary_mappings: Optional dict of mappings to be written to a CSV file passed to suggest_summaries --mappings
        :param expected_report_summary: The value of the normalised_report_summary field on the GoodOnApplication
        """
        application = StandardApplicationFactory.create(organisation=self.organisation)
        good = GoodFactory.create(
            organisation=self.organisation,
        )

        good_on_application_pk = GoodOnApplicationFactory.create(
            application=application, good=good, report_summary=report_summary, is_good_controlled=True
        ).pk

        normalised_report_summary = (
            (
                annotate_normalised_summary(
                    GoodOnApplication.objects.filter(id=good_on_application_pk), report_summary_mappings
                )
            )
            .get()
            .normalised_report_summary
        )

        assert expected_report_summary == normalised_report_summary


class SuggestedSummariesManagementCommand(DataTestClient):
    @parameterized.expand(
        [
            (
                # Data provided without remappings for mis-spellings
                [
                    # report_summary, suggested_prefix, suggested_subject
                    ("arts and crafts", None, "arts and crafts"),
                    ("training for arts and crafts", "training for", "arts and crafts"),
                    ("equipment for arts and crafts", "equipment for", "arts and crafts"),
                    ("tf arts and crafts", None, None),
                ],
                None,
            ),
            (
                # Data provided with remappings for mis-spellings
                [
                    # report_summary, suggested_prefix, suggested_subject
                    ("arts and crafts", None, "arts and crafts"),
                    ("training for arts and crafts", "training for", "arts and crafts"),
                    ("equipment for arts and crafts", "equipment for", "arts and crafts"),
                    ("trf arts and crafts", None, None),
                    ("tf arts and crafts", "training for", "arts and crafts"),
                ],
                # report_summary_mappings: report summaries listed as the key here should be remapped to the value,
                # which in turn may allow the management command to find a matching ReportSummaryPrefix and
                # ReportSummarySubject.
                {"tf arts and crafts": "training for arts and crafts"},
            ),
        ]
    )
    def test_management_command(self, report_data, report_summary_mappings: Optional[Dict[str, str]]):
        """
        Test that the management command produces a CSV file with the expected rows.

        Controlled GoodOnApplications are created with a report summary and no prefix or subject,
        the management command is run and the output is checked to verify the GoodOnApplications
        with the expected ids, report summaries, suggested prefixes and subjects are present.

        Data normalisation is not tested here, see: `test_annotate_normalised_summary_annotation`.

        :param report_data: A list of tuples containing the report_summary, suggested_prefix and suggested_subject

        This data is used to create GoodOnApplications with the given report_summary and no prefix or subject,
        and then to build the expected content of the csv file the management command should output.

        :param report_summary_mappings: Optional dict of mappings to be written to a CSV file passed to suggest_summaries --mappings
        """
        application = StandardApplicationFactory.create(organisation=self.organisation)
        good = GoodFactory.create(
            organisation=self.organisation,
        )

        # Create a GoodOnApplication that should NOT match and prefixes or suffixes or appear in the final CSV:
        unmappable_good_on_application = GoodOnApplicationFactory.create(
            application=application, good=good, report_summary="xyz _unmappable", is_good_controlled=True
        )

        # Dict of {report_summary: optional_instance: ReportSummaryPrefix }
        # for prefixes that are expected to be matched by the management command.
        # will have None as the value (the corresponding entry in the CSV will have a blank value for the prefix).
        report_prefixes: Dict[str, Optional[ReportSummaryPrefix]] = {
            report_summary: ReportSummaryPrefix.objects.get_or_create(name=suggested_prefix)[0]
            if suggested_prefix
            else None
            for report_summary, suggested_prefix, suggested_subject in report_data
            if suggested_subject
        }

        # Dict of {"report_summary": instance: ReportSummarySubject}
        # for subjects that are expected to be matched by the management command.
        report_subjects: Dict[str, ReportSummarySubject] = {
            report_summary: ReportSummarySubject.objects.get_or_create(name=suggested_subject, code_level=1)[0]
            for report_summary, _, suggested_subject in report_data
            if suggested_subject
        }

        # List of tuples of:
        #   (new GoodOnApplication instance, optional ReportSummaryPrefix instance, ReportSummarySubject instance)
        good_on_application_suggestions = [
            (
                GoodOnApplicationFactory.create(
                    application=application, good=good, report_summary=report_summary, is_good_controlled=True
                ),
                report_prefixes[report_summary],
                report_subjects[report_summary],
            )
            for report_summary, _suggested_prefix, suggested_subject in report_data
            if suggested_subject
        ]

        expected_csv_file_lines = self._get_suggestions_as_csv_lines(good_on_application_suggestions)
        expected_unmappable_lines = self._get_suggestions_as_csv_lines([(unmappable_good_on_application, None, None)])

        # Inside a temporary directory, run the management command there and then verify that the file
        # contents match the data in expected_csv_file_lines:
        with tempfile.TemporaryDirectory(suffix="-test_suggest_summaries") as tmpdirname:
            options = {}
            if report_summary_mappings:
                mappings_filename = tmpdirname + "/mappings.csv"
                options = {"mappings": mappings_filename}
                self._save_report_summaries_corrections_csv(report_summary_mappings, mappings_filename)

            csv_file_path = Path(tmpdirname) / "suggested_summaries.csv"
            with contextlib.redirect_stderr(StringIO()) as stderr:
                call_command("suggest_summaries", csv_file_path.as_posix(), **options)

            # Expect a CSV header and the single unmappable good on application with no suggestions:
            unmappable_file_lines = stderr.getvalue().splitlines()
            assert unmappable_file_lines == expected_unmappable_lines

            # Expect a CSV header and the suggestions for the good on applications with report summaries
            assert csv_file_path.exists()

            actual_file_lines = csv_file_path.read_text().splitlines()

            self.assertCountEqual(expected_csv_file_lines, actual_file_lines)

    @parameterized.expand([(True,), (False,)])
    def test_unmappable_items_are_written_to_stderr(self, create_umappable_good_on_application):
        """
        Any unmappable GoodOnApplications should be written to stderr in the same CSV format as the output file.
        If there are no files, there is no output.
        """
        application = StandardApplicationFactory.create(organisation=self.organisation)
        good = GoodFactory.create(
            organisation=self.organisation,
        )

        if create_umappable_good_on_application:
            unmappable_good_on_application = GoodOnApplicationFactory.create(
                application=application, good=good, report_summary="ijk _unmappable", is_good_controlled=True
            )
            expected_unmappable_lines = self._get_suggestions_as_csv_lines(
                [(unmappable_good_on_application, None, None)]
            )
        else:
            # No unmappable good on applications are created, so no lines are expected in the stderr output
            expected_unmappable_lines = []

        # No report summary mappings are provided, so all GoodOnApplications should be unmappable, resulting in
        # a CSV containing just a header.
        expected_csv_file_lines = [
            '"id","report_summary","suggested_prefix","suggested_prefix_id","suggested_subject","suggested_subject_id"'
        ]

        with tempfile.TemporaryDirectory(suffix="-test_suggest_summaries") as tmpdirname:
            csv_file_path = Path(tmpdirname) / "suggested_summaries.csv"
            with contextlib.redirect_stderr(StringIO()) as stderr:
                call_command("suggest_summaries", csv_file_path.as_posix())

            # Expect a CSV header and the single unmappable good on application with no suggestions:
            unmappable_file_lines = stderr.getvalue().splitlines()
            assert unmappable_file_lines == expected_unmappable_lines

            # Expect a CSV header and the suggestions for the good on applications with report summaries
            assert csv_file_path.exists()

            actual_file_lines = csv_file_path.read_text().splitlines()

            self.assertCountEqual(expected_csv_file_lines, actual_file_lines)

    def _get_suggestions_as_csv_lines(
        self,
        good_on_application_suggestions: List[
            Tuple[GoodOnApplication, Optional[ReportSummaryPrefix], Optional[ReportSummarySubject]]
        ],
    ) -> List[str]:
        """
        Build a list of strings representing the expected content of the CSV file the management command.

        This is intended to be compared with the actual file content read with .splitlines()
        """
        # Each field in the output CSV is quoted: illustrative example:
        # "id","report_summary","suggested_prefix","suggested_prefix_id","suggested_subject","suggested_subject_id"
        # "01234567-89ab-cdef-0123-456789abcdef","drawing supplies pens (1)","drawing supplies","01234567-89ab-cdef-0123-456789abcdef","pens","01234567-89ab-cdef-0123-456789abcdef"
        #
        # Template used to generate data in the above format for all the non header rows, using str.format:
        csv_row_template = (
            '"{good_on_application_id}",'
            + '"{report_summary}",'
            + '"{suggested_prefix}",'
            + '"{suggested_prefix_id}",'
            + '"{suggested_subject}",'
            + '"{suggested_subject_id}"'
        )

        # All the data expected in the CSV file the management command will output as a list of strings
        # including the header.
        # Rows are output by iterating the data in expected_good_on_application_suggestions and passing it to
        # expected_csv_row_template.format() to generate the string for each row.
        csv_file_lines = [
            # Header, as a string:
            '"id","report_summary","suggested_prefix","suggested_prefix_id","suggested_subject","suggested_subject_id"',
            # Data rows as strings, for the following lines:
            *[
                csv_row_template.format(
                    good_on_application_id=str(good_on_application.pk),
                    report_summary=good_on_application.report_summary,
                    suggested_prefix=suggested_prefix.name if suggested_prefix else "",
                    suggested_prefix_id=str(suggested_prefix.id) if suggested_prefix else "",
                    suggested_subject=suggested_subject.name if suggested_subject else "",
                    suggested_subject_id=str(suggested_subject.id) if suggested_subject else "",
                )
                for (
                    good_on_application,
                    suggested_prefix,
                    suggested_subject,
                ) in good_on_application_suggestions
            ],
        ]
        return csv_file_lines

    def _save_report_summaries_corrections_csv(self, report_summary_mappings: Dict[str, str], filename: str):
        """Write CSV file for consumption by suggest_summaries --mappings.

        :param report_summary_mappings: Each (key: value) is written to a row in the mappings csv
        `as (original_report_summary, corrected_report_summary).
        """
        with open(filename, "w") as mappings_file:
            csv_mappings_writer = csv.writer(mappings_file, quoting=csv.QUOTE_ALL)
            csv_mappings_writer.writerow(["original_report_summary", "corrected_report_summary"])
            csv_mappings_writer.writerows(report_summary_mappings.items())
