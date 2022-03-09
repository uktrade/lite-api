from parameterized import parameterized

from django.urls import reverse

from api.applications.tests.factories import GoodFactory, GoodOnApplicationFactory, StandardApplicationFactory
from api.goods.models import FirearmGoodDetails
from api.goods.tests.factories import FirearmFactory
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class ApplicationsRequiresSerialNumbersListTests(DataTestClient):
    def setUp(self):
        super().setUp()

        self.url = reverse("applications:require_serial_numbers")

    @parameterized.expand(
        [
            (CaseStatusEnum.SUBMITTED, FirearmGoodDetails.SerialNumberAvailability.AVAILABLE),
            (CaseStatusEnum.SUBMITTED, FirearmGoodDetails.SerialNumberAvailability.LATER),
            (CaseStatusEnum.FINALISED, FirearmGoodDetails.SerialNumberAvailability.AVAILABLE),
            (CaseStatusEnum.FINALISED, FirearmGoodDetails.SerialNumberAvailability.LATER),
        ],
    )
    def test_returned_application_requiring_serial_numbers(self, case_status, serial_numbers_available):
        application = StandardApplicationFactory(
            organisation=self.organisation, status=get_case_status_by_status(case_status)
        )
        good = GoodFactory(
            organisation=self.organisation,
        )
        firearm_details = FirearmFactory(
            serial_numbers_available=serial_numbers_available,
            serial_numbers=[],
            number_of_items=3,
        )
        GoodOnApplicationFactory(
            application=application,
            firearm_details=firearm_details,
            good=good,
        )

        response = self.client.get(self.url, **self.exporter_headers)
        content = response.json()
        self.assertEqual(content["count"], 1)
        self.assertEqual(content["results"][0]["id"], str(application.pk))

    @parameterized.expand(
        [
            CaseStatusEnum.SUBMITTED,
            CaseStatusEnum.FINALISED,
        ],
    )
    def test_returned_application_not_requiring_serial_numbers_because_unavailable(self, case_status):
        application = StandardApplicationFactory(
            organisation=self.organisation, status=get_case_status_by_status(case_status)
        )
        good = GoodFactory(
            organisation=self.organisation,
        )
        firearm_details = FirearmFactory(
            serial_numbers_available=FirearmGoodDetails.SerialNumberAvailability.NOT_AVAILABLE,
        )
        GoodOnApplicationFactory(
            application=application,
            firearm_details=firearm_details,
            good=good,
        )

        response = self.client.get(self.url, **self.exporter_headers)
        content = response.json()
        self.assertEqual(content["count"], 0)

    @parameterized.expand(
        [
            (CaseStatusEnum.SUBMITTED, FirearmGoodDetails.SerialNumberAvailability.AVAILABLE),
            (CaseStatusEnum.SUBMITTED, FirearmGoodDetails.SerialNumberAvailability.LATER),
            (CaseStatusEnum.FINALISED, FirearmGoodDetails.SerialNumberAvailability.AVAILABLE),
            (CaseStatusEnum.FINALISED, FirearmGoodDetails.SerialNumberAvailability.LATER),
        ],
    )
    def test_returned_application_not_requiring_serial_numbers_because_all_filled(
        self, case_status, serial_numbers_available
    ):
        application = StandardApplicationFactory(
            organisation=self.organisation, status=get_case_status_by_status(case_status)
        )
        good = GoodFactory(
            organisation=self.organisation,
        )
        firearm_details = FirearmFactory(
            serial_numbers_available=serial_numbers_available,
            serial_numbers=["1111", "2222", "3333"],
            number_of_items=3,
        )
        GoodOnApplicationFactory(
            application=application,
            firearm_details=firearm_details,
            good=good,
        )

        response = self.client.get(self.url, **self.exporter_headers)
        content = response.json()
        self.assertEqual(content["count"], 0)
