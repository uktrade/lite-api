import csv
import tempfile
from pathlib import Path

from django.core.management import call_command
from parameterized import parameterized


from api.applications.management.commands.suggest_summaries import annotate_normalised_summary
from api.applications.models import GoodOnApplication
from api.applications.tests.factories import GoodOnApplicationFactory, StandardApplicationFactory
from api.goods.tests.factories import GoodFactory
from api.staticdata.report_summaries.models import ReportSummaryPrefix, ReportSummarySubject
from test_helpers.clients import DataTestClient


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
                    ("tf arts and crafts", "training for", "arts and crafts"),
                    ("trf arts and crafts", None, None),
                ],
                [
                    ("tf arts and crafts", "training for arts and crafts"),
                ],
            ),
        ]
    )
    def test_management_command(self, report_data, mappings):
        """
        Test that the management command produces a CSV file with the expected rows.

        Controlled GoodOnApplications are created with a report summary and no prefix or subject,
        the management command is run and the output is checked to verify the GoodOnApplications
        with the expected ids, report summaries, suggested prefixes and subjects are present.

        Data normalisation is not tested here, see: `test_annotate_normalised_summary_annotation`.
        """
        application = StandardApplicationFactory.create(organisation=self.organisation)
        good = GoodFactory.create(
            organisation=self.organisation,
        )

        # Build a dict of report_summaries and the ReportSummaryPrefix instances that should be matched with them.
        # Where there is no suggested prefix the value is None (having an empty prefix is valid but a populated
        # subject is valid).
        expected_report_prefixes = {
            report_summary: ReportSummaryPrefix.objects.get_or_create(name=suggested_prefix)[0]
            if suggested_prefix
            else None
            for report_summary, suggested_prefix, suggested_subject in report_data
            if suggested_subject
        }

        # Build a dict of report_summaries and the ReportSummarySubject instances that should be matched with them.
        expected_report_subjects = {
            report_summary: ReportSummarySubject.objects.get_or_create(name=suggested_subject, code_level=1)[0]
            for report_summary, _, suggested_subject in report_data
            if suggested_subject
        }

        # The data we expect to find in the CSV file and corresponding GoodOnApplications
        expected_good_on_application_suggestions = [
            (
                GoodOnApplicationFactory.create(
                    application=application, good=good, report_summary=report_summary, is_good_controlled=True
                ),
                expected_report_prefixes[report_summary],
                expected_report_subjects[report_summary],
            )
            for report_summary, _suggested_prefix, suggested_subject in report_data
            if suggested_subject
        ]

        # GoodOnApplication that should not match and prefixes or suffixes or appear in the final CSV:
        GoodOnApplicationFactory.create(
            application=application, good=good, report_summary="xyz _unmappable", is_good_controlled=True
        )

        expected_csv_row_template = (
            '"{good_on_application_id}",'
            + '"{report_summary}",'
            + '"{suggested_prefix}",'
            + '"{suggested_prefix_id}",'
            + '"{suggested_subject}",'
            + '"{suggested_subject_id}"'
        )

        expected_csv_rows = [
            '"id","report_summary","suggested_prefix","suggested_prefix_id","suggested_subject","suggested_subject_id"',
            *[
                expected_csv_row_template.format(
                    good_on_application_id=str(good_on_application.pk),
                    report_summary=good_on_application.report_summary,
                    suggested_prefix=suggested_prefix.name if suggested_prefix else "",
                    suggested_prefix_id=str(suggested_prefix.id) if suggested_prefix else "",
                    suggested_subject=suggested_subject.name,
                    suggested_subject_id=str(suggested_subject.id),
                )
                for (
                    good_on_application,
                    suggested_prefix,
                    suggested_subject,
                ) in expected_good_on_application_suggestions
            ],
        ]

        with tempfile.TemporaryDirectory(suffix="-test_suggest_summaries") as tmpdirname:
            options = {}
            if mappings:
                mappings_filename = tmpdirname + "/mappings.csv"
                options = {"mappings": mappings_filename}
                with open(mappings_filename, "w") as mappings_file:
                    csv_mappings_writer = csv.writer(mappings_file, quoting=csv.QUOTE_ALL)
                    csv_mappings_writer.writerow(["original_report_summary", "corrected_report_summary"])
                    csv_mappings_writer.writerows(mappings)

            csv_path = Path(tmpdirname) / "suggested_summaries.csv"
            call_command("suggest_summaries", csv_path.as_posix(), **options)

            assert csv_path.exists()

            csv_rows = csv_path.read_text().splitlines()

            self.assertCountEqual(expected_csv_rows, csv_rows)
