from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestPopulateReportSummariesDataMigration(MigratorTestCase):

    migrate_from = ("report_summaries", "0006_reportsummary")
    migrate_to = ("report_summaries", "0007_populate_report_summaries")

    def test_0007_populating_report_summaries(self):
        ReportSummaryPrefix = self.old_state.apps.get_model("report_summaries", "ReportSummaryPrefix")
        ReportSummarySubject = self.old_state.apps.get_model("report_summaries", "ReportSummarySubject")
        ReportSummary = self.old_state.apps.get_model("report_summaries", "ReportSummary")

        prefix_ids = [""] + list(map(lambda x: str(x), ReportSummaryPrefix.objects.values_list("id", flat=True)))
        subject_ids = list(map(lambda x: str(x), ReportSummarySubject.objects.values_list("id", flat=True)))

        report_summary_combinations = [(prefix, subject) for prefix in prefix_ids for subject in subject_ids]

        self.assertEqual(ReportSummary.objects.count(), len(report_summary_combinations))
