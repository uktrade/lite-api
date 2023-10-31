from pytz import timezone

from api.flags.enums import SystemFlags
from parameterized import parameterized
from api.goods.enums import GoodStatus
from api.staticdata.control_list_entries.models import ControlListEntry
from api.staticdata.regimes.models import RegimeEntry
from api.staticdata.report_summaries.models import ReportSummarySubject, ReportSummaryPrefix
from test_helpers.clients import DataTestClient
from api.applications.tests.factories import GoodOnApplicationFactory
from django.urls import reverse


class GoodPrecedentsListViewTests(DataTestClient):
    def setUp(self):
        super().setUp()

        # Create a common good
        self.good = self.create_good("A good", self.organisation)
        self.good.flags.add(SystemFlags.WASSENAAR)
        # Create an application
        self.draft_1 = self.create_draft_standard_application(self.organisation)
        self.gona_1 = GoodOnApplicationFactory(
            good=self.good, application=self.draft_1, quantity=5, report_summary="test1"
        )
        self.case = self.submit_application(self.draft_1)
        self.case.queues.set([self.queue])

        # Create another application
        self.draft_2 = self.create_draft_standard_application(self.organisation)
        self.gona_2 = GoodOnApplicationFactory(
            good=self.good,
            application=self.draft_2,
            quantity=10,
            report_summary="test2",
            is_good_controlled=True,
            is_ncsc_military_information_security=False,
            comment="Classic product",
        )
        self.gona_2.control_list_entries.add(ControlListEntry.objects.get(rating="ML1a"))
        self.gona_2.regime_entries.add(RegimeEntry.objects.get(name="Wassenaar Arrangement"))
        self.gona_2.report_summary_prefix = ReportSummaryPrefix.objects.get(name="components for")
        self.gona_2.report_summary_subject = ReportSummarySubject.objects.get(name="neural computers")
        self.gona_2.save()

        # Expect this to be missing from API responses as is_good_controlled=None
        self.gona_3 = GoodOnApplicationFactory(
            good=self.good,
            application=self.draft_2,
            quantity=10,
            report_summary="test2",
            is_good_controlled=None,
            is_ncsc_military_information_security=False,
            comment="Classic product",
        )
        self.submit_application(self.draft_2)
        self.url = reverse("cases:good_precedents", kwargs={"pk": self.case.id})

    @parameterized.expand([GoodStatus.DRAFT, GoodStatus.SUBMITTED, GoodStatus.QUERY])
    def test_get_no_matching_precedents(self, status):
        self.good.status = status
        self.good.save()
        response = self.client.get(self.url, **self.gov_headers)
        assert response.status_code == 200
        json = response.json()
        assert json["count"] == 0

    def test_get_with_matching_precedents(self):
        self.good.status = GoodStatus.VERIFIED
        self.good.save()
        response = self.client.get(self.url, **self.gov_headers)
        assert response.status_code == 200
        json = response.json()
        wassenaar_regime = RegimeEntry.objects.get(name="Wassenaar Arrangement")
        assert json == {
            "count": 1,
            "total_pages": 1,
            "results": [
                {
                    "id": str(self.gona_2.id),
                    "queue": None,
                    "application": str(self.draft_2.id),
                    "reference": self.draft_2.reference_code,
                    "good": str(self.good.id),
                    "report_summary": "test2",
                    "quantity": 10.0,
                    "unit": None,
                    "value": None,
                    "control_list_entries": ["ML1a"],
                    "destinations": ["Great Britain"],
                    "wassenaar": True,
                    "submitted_at": self.draft_2.submitted_at.astimezone(timezone("UTC")).strftime(
                        "%Y-%m-%dT%H:%M:%S.%fZ"
                    ),
                    "goods_starting_point": "",
                    "regime_entries": [
                        {
                            "name": "Wassenaar Arrangement",
                            "pk": str(wassenaar_regime.id),
                            "shortened_name": "W",
                            "subsection": {
                                "name": "Wassenaar Arrangement",
                                "pk": str(wassenaar_regime.subsection.id),
                                "regime": {"name": "WASSENAAR", "pk": str(wassenaar_regime.subsection.regime.id)},
                            },
                        }
                    ],
                    "is_good_controlled": True,
                    "is_ncsc_military_information_security": False,
                    "comment": "Classic product",
                    "report_summary_prefix": {
                        "id": "42e813cb-a75c-4f60-a121-dbe949222dd8",  # /PS-IGNORE
                        "name": "components for",
                    },
                    "report_summary_subject": {
                        "id": "266cb5b0-85ad-49fb-8d8e-a742af9ebb4b",  # /PS-IGNORE
                        "name": "neural computers",
                    },
                }
            ],
        }
