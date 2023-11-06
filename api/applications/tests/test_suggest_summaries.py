from parameterized import parameterized


from api.applications.management.commands.suggest_summaries import annotate_normalised_summary
from api.applications.models import GoodOnApplication
from api.applications.tests.factories import GoodOnApplicationFactory, StandardApplicationFactory
from api.goods.tests.factories import GoodFactory
from test_helpers.clients import DataTestClient


class SuggestedSummariesTest(DataTestClient):
    @parameterized.expand(
        [
            ("lower case", "lower case"),
            ("UPPER CASE", "upper case"),
            ("Mixed Case", "mixed case"),
            ("contains a bracketed number (1)", "contains a bracketed number"),
            ("contains a bracketed x (x)", "contains a bracketed x"),
        ],
    )
    def test_annotate_normalised_summary(self, report_summary, expected_normalised_report_summary):
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
