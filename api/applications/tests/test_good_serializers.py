from api.applications.serializers.good import GoodOnApplicationViewSerializer
from api.applications.tests.factories import StandardApplicationFactory, GoodOnApplicationFactory
from api.goods.tests.factories import GoodFactory
from api.staticdata.report_summaries.models import ReportSummaryPrefix, ReportSummarySubject
from test_helpers.clients import DataTestClient


class GoodSerializerInternalTests(DataTestClient):
    def setUp(self):
        super().setUp()

        application = StandardApplicationFactory.create()
        good = GoodFactory.create(organisation=self.organisation)

        self.good_on_application = GoodOnApplicationFactory.create(
            application=application,
            good=good,
        )
        self.good_on_application.report_summary_prefix = ReportSummaryPrefix.objects.first()
        self.good_on_application.report_summary_subject = ReportSummarySubject.objects.first()

    def test_report_summary_present(self):
        serialized_data = GoodOnApplicationViewSerializer(self.good_on_application).data
        actual_prefix = serialized_data["report_summary_prefix"]
        actual_subject = serialized_data["report_summary_subject"]

        self.assertEqual(actual_prefix["id"], str(self.good_on_application.report_summary_prefix.id))
        self.assertEqual(actual_prefix["name"], self.good_on_application.report_summary_prefix.name)
        self.assertEqual(actual_subject["id"], str(self.good_on_application.report_summary_subject.id))
        self.assertEqual(actual_subject["name"], self.good_on_application.report_summary_subject.name)
