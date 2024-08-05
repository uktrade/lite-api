from typing import Tuple, List

from pytz import timezone

from api.applications.models import StandardApplication, GoodOnApplication
from api.applications.tests.factories import DraftStandardApplicationFactory
from api.flags.enums import SystemFlags
from parameterized import parameterized
from api.goods.enums import GoodStatus
from api.goods.tests.factories import GoodFactory
from api.staticdata.control_list_entries.models import ControlListEntry
from api.staticdata.regimes.models import RegimeEntry
from api.staticdata.report_summaries.models import ReportSummarySubject, ReportSummaryPrefix
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient
from api.applications.tests.factories import GoodOnApplicationFactory
from django.urls import reverse


class GoodPrecedentsListViewTests(DataTestClient):
    def setUp(self):
        super().setUp()

        # Create a common good
        self.good = GoodFactory(organisation=self.organisation)
        self.good.flags.add(SystemFlags.WASSENAAR)
        # Create an application
        self.application = self.create_draft_standard_application(self.organisation)
        GoodOnApplicationFactory.create(
            good=self.good, application=self.application, quantity=5, report_summary="test1"
        )
        self.case = self.submit_application(self.application)
        self.case.queues.set([self.queue])

        # Create precedents that should be returned
        self.precedents: List[Tuple[StandardApplication, GoodOnApplication]] = []
        for status in CaseStatusEnum.precedent_statuses:
            precedent_application = self.create_draft_standard_application(self.organisation)
            goa = GoodOnApplicationFactory(
                good=self.good,
                application=precedent_application,
                quantity=10,
                report_summary="test2",
                is_good_controlled=True,
                is_ncsc_military_information_security=False,
                comment="Classic product",
            )
            goa.control_list_entries.add(ControlListEntry.objects.get(rating="ML1a"))
            goa.regime_entries.add(RegimeEntry.objects.get(name="Wassenaar Arrangement"))
            goa.report_summary_prefix = ReportSummaryPrefix.objects.get(name="components for")
            goa.report_summary_subject = ReportSummarySubject.objects.get(name="neural computers")
            goa.save()

            self.submit_application(precedent_application)

            precedent_application.status = get_case_status_by_status(status)
            precedent_application.save()

            self.precedents.append(tuple((precedent_application, goa)))

        # Expect this to be missing from API responses as is_good_controlled=None
        GoodOnApplicationFactory.create(
            good=self.good,
            application=self.precedents[0][0],
            quantity=10,
            report_summary="test2",
            is_good_controlled=None,
            is_ncsc_military_information_security=False,
            comment="Classic product",
        )

        unwanted_draft_application = self.create_draft_standard_application(self.organisation)
        goa = GoodOnApplicationFactory(
            good=self.good,
            application=unwanted_draft_application,
            quantity=10,
            report_summary="test2",
            is_good_controlled=True,
            is_ncsc_military_information_security=False,
            comment="Classic product",
        )
        goa.control_list_entries.add(ControlListEntry.objects.get(rating="ML1a"))
        goa.regime_entries.add(RegimeEntry.objects.get(name="Wassenaar Arrangement"))
        goa.report_summary_prefix = ReportSummaryPrefix.objects.get(name="components for")
        goa.report_summary_subject = ReportSummarySubject.objects.get(name="neural computers")
        goa.save()

        self.submit_application(unwanted_draft_application)

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
        assert len(CaseStatusEnum.precedent_statuses) > 0  # Sanity check

        self.good.status = GoodStatus.VERIFIED
        self.good.save()

        response = self.client.get(self.url, **self.gov_headers)
        assert response.status_code == 200

        json = response.json()

        # The helper function that creates application uses factories to add parties to application
        # so their destinations will be different hence extract expected values instead of using
        # fixed values in expected_data
        expected_destinations = sorted(
            list(set(self.application.parties.values_list("party__country__name", flat=True)))
        )

        wassenaar_regime = RegimeEntry.objects.get(name="Wassenaar Arrangement")
        expected_data = {
            "count": len(CaseStatusEnum.precedent_statuses),
            "total_pages": 1,
            "results": [
                {
                    "id": str(good_on_application.id),
                    "queue": None,
                    "application": str(application.id),
                    "reference": application.reference_code,
                    "good": str(self.good.id),
                    "report_summary": "test2",
                    "quantity": 10.0,
                    "unit": None,
                    "value": None,
                    "control_list_entries": ["ML1a"],
                    "destinations": expected_destinations,
                    "wassenaar": True,
                    "submitted_at": application.submitted_at.astimezone(timezone("UTC")).strftime(
                        "%Y-%m-%dT%H:%M:%S.%f"
                    )[:-3]
                    + "Z",
                    "goods_starting_point": "GB",
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
                for application, good_on_application in self.precedents
            ],
        }

        assert json == expected_data

    @parameterized.expand(CaseStatusEnum.precedent_statuses)
    def test_get_expected_previous_assessments(self, status):
        good = GoodFactory(organisation=self.organisation)
        good.flags.add(SystemFlags.WASSENAAR)

        precedent_application = DraftStandardApplicationFactory(organisation=self.organisation)
        good_on_application = GoodOnApplicationFactory(
            good=good,
            application=precedent_application,
            quantity=1000,
            report_summary="analogue-to-digital converters",
            is_good_controlled=True,
            comment="12-bit ADC",
        )
        good_on_application.control_list_entries.add(ControlListEntry.objects.get(rating="ML1a"))
        good_on_application.regime_entries.add(RegimeEntry.objects.get(name="Wassenaar Arrangement"))
        good_on_application.report_summary_prefix = ReportSummaryPrefix.objects.get(name="components for")
        good_on_application.report_summary_subject = ReportSummarySubject.objects.get(name="neural computers")
        good_on_application.save()

        self.submit_application(precedent_application)

        precedent_application.status = get_case_status_by_status(status)
        precedent_application.save()

        # Good status becomes verified once it is assessed
        good.status = GoodStatus.VERIFIED
        good.save()

        # Reuse the same good from the previous application and ensure that
        # assessment given previously comes up as precedent
        application = DraftStandardApplicationFactory(organisation=self.organisation)
        GoodOnApplicationFactory(
            good=good,
            application=application,
            quantity=1000,
            report_summary="analogue-to-digital converters",
            is_good_controlled=True,
        )
        case = self.submit_application(application)
        application.status = get_case_status_by_status(CaseStatusEnum.INITIAL_CHECKS)
        application.save()

        url = reverse("cases:good_precedents", kwargs={"pk": case.id})
        response = self.client.get(url, **self.gov_headers)
        assert response.status_code == 200

        json = response.json()
        wassenaar_regime = RegimeEntry.objects.get(name="Wassenaar Arrangement")
        expected = {
            "count": 1,
            "results": [
                {
                    "application": str(precedent_application.id),
                    "comment": "12-bit ADC",
                    "control_list_entries": ["ML1a"],
                    "destinations": ["Italy", "Spain"],
                    "good": str(good_on_application.good.id),
                    "goods_starting_point": "GB",
                    "id": str(good_on_application.id),
                    "is_good_controlled": True,
                    "is_ncsc_military_information_security": None,
                    "quantity": 1000.0,
                    "queue": None,
                    "reference": precedent_application.reference_code,
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
                    "report_summary": "analogue-to-digital converters",
                    "report_summary_prefix": {
                        "id": str(good_on_application.report_summary_prefix.id),
                        "name": good_on_application.report_summary_prefix.name,
                    },
                    "report_summary_subject": {
                        "id": str(good_on_application.report_summary_subject.id),
                        "name": good_on_application.report_summary_subject.name,
                    },
                    "submitted_at": precedent_application.submitted_at.astimezone(timezone("UTC")).strftime(
                        "%Y-%m-%dT%H:%M:%S.%f"
                    )[:-3]
                    + "Z",
                    "unit": None,
                    "value": None,
                    "wassenaar": True,
                }
            ],
            "total_pages": 1,
        }

        assert expected == json

    @parameterized.expand(CaseStatusEnum.non_precedent_statuses)
    def test_do_not_expect_previous_assessments(self, status):
        good = GoodFactory(organisation=self.organisation)
        good.flags.add(SystemFlags.WASSENAAR)

        precedent_application = DraftStandardApplicationFactory(organisation=self.organisation)
        good_on_application = GoodOnApplicationFactory(
            good=good,
            application=precedent_application,
            quantity=1000,
            report_summary="analogue-to-digital converters",
            is_good_controlled=True,
            comment="12-bit ADC",
        )
        good_on_application.control_list_entries.add(ControlListEntry.objects.get(rating="ML1a"))
        good_on_application.regime_entries.add(RegimeEntry.objects.get(name="Wassenaar Arrangement"))
        good_on_application.report_summary_prefix = ReportSummaryPrefix.objects.get(name="components for")
        good_on_application.report_summary_subject = ReportSummarySubject.objects.get(name="neural computers")
        good_on_application.save()

        self.submit_application(precedent_application)

        precedent_application.status = get_case_status_by_status(status)
        precedent_application.save()

        # Reuse the same good from the previous application and ensure that
        # assessment given previously does not come up as precedent
        application = DraftStandardApplicationFactory(organisation=self.organisation)
        GoodOnApplicationFactory(
            good=good,
            application=application,
            quantity=1000,
            report_summary="analogue-to-digital converters",
            is_good_controlled=True,
        )
        case = self.submit_application(application)
        application.status = get_case_status_by_status(CaseStatusEnum.INITIAL_CHECKS)
        application.save()

        url = reverse("cases:good_precedents", kwargs={"pk": case.id})
        response = self.client.get(url, **self.gov_headers)
        assert response.status_code == 200
        assert response.json() == {
            "count": 0,
            "results": [],
            "total_pages": 1,
        }
