import random

from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestBackPopulateReportSummariesDataMigration(MigratorTestCase):

    migrate_from = ("report_summaries", "0007_populate_report_summaries")
    migrate_to = ("report_summaries", "0008_back_populate_multiple_ars_data")

    def prepare(self):
        Organisation = self.old_state.apps.get_model("organisations", "Organisation")
        StandardApplication = self.old_state.apps.get_model("applications", "StandardApplication")
        Good = self.old_state.apps.get_model("goods", "Good")
        GoodOnApplication = self.old_state.apps.get_model("applications", "GoodOnApplication")
        ReportSummaryPrefix = self.old_state.apps.get_model("report_summaries", "ReportSummaryPrefix")
        ReportSummarySubject = self.old_state.apps.get_model("report_summaries", "ReportSummarySubject")

        prefixes = list(ReportSummaryPrefix.objects.values_list("id", flat=True))
        subjects = list(ReportSummarySubject.objects.values_list("id", flat=True))

        # create few GoodOnApplication objects for SIEL with the same Good
        organisation = Organisation.objects.create(name="Exporter")
        application = StandardApplication.objects.create(
            name="test", organisation=organisation, case_type_id="00000000-0000-0000-0000-000000000004"
        )
        good1 = Good.objects.create(name="controlled good", organisation=organisation)
        good2 = Good.objects.create(name="non-controlled good", organisation=organisation)
        self.controlled_goods = [
            GoodOnApplication.objects.create(
                application=application,
                good=good1,
                is_good_controlled=True,
                report_summary_prefix_id=random.choice(prefixes),
                report_summary_subject_id=random.choice(subjects),
            )
            for i in range(5)
        ]
        self.non_controlled_goods = [
            GoodOnApplication.objects.create(application=application, good=good2, is_good_controlled=False)
            for i in range(5)
        ]

        self.assertEqual(GoodOnApplication.objects.filter(report_summaries__isnull=True).count(), 10)

    def test_0008_back_populate_multiple_ars_data(self):
        GoodOnApplication = self.new_state.apps.get_model("applications", "GoodOnApplication")

        expected_ids = [item.id for item in self.controlled_goods]
        actual_ids = list(
            GoodOnApplication.objects.filter(
                is_good_controlled=True,
                report_summaries__isnull=False,
            ).values_list("id", flat=True)
        )
        self.assertEqual(actual_ids, expected_ids)

        expected_ids = [item.id for item in self.non_controlled_goods]
        actual_ids = list(
            GoodOnApplication.objects.filter(
                is_good_controlled=False,
                report_summaries__isnull=True,
            ).values_list("id", flat=True)
        )
        self.assertEqual(actual_ids, expected_ids)
