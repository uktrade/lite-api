from decimal import Decimal

from django.utils import timezone

from applications.tests.factories import StandardApplicationFactory, GoodOnApplicationFactory
from api.goods.tests.factories import GoodFactory
from licences.enums import LicenceStatus
from licences.service import get_case_licences
from licences.tests.factories import LicenceFactory, GoodOnLicenceFactory
from test_helpers.clients import DataTestClient


class GetCaseLicenceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.application = StandardApplicationFactory()
        self.licence = LicenceFactory(
            case=self.application,
            start_date=timezone.now().date(),
            status=LicenceStatus.REVOKED,
            duration=100,
            reference_code="reference",
        )
        self.good = GoodFactory(organisation=self.application.organisation)
        self.good_on_application = GoodOnApplicationFactory(
            application=self.application, good=self.good, quantity=100.0, value=Decimal("1000.00")
        )
        self.good_on_licence = GoodOnLicenceFactory(
            good=self.good_on_application,
            quantity=self.good_on_application.quantity,
            usage=20.0,
            value=20,
            licence=self.licence,
        )

    def test_get_application_licences(self):
        data = get_case_licences(self.application)[0]
        self.assertEqual(data["id"], str(self.licence.id))
        self.assertEqual(data["reference_code"], self.licence.reference_code)
        self.assertEqual(data["status"], LicenceStatus.to_str(self.licence.status))
        self.assertEqual(data["goods"][0]["control_list_entries"], [])
        self.assertEqual(data["goods"][0]["description"], self.good.description)
        self.assertEqual(data["goods"][0]["quantity"], self.good_on_licence.quantity)
        self.assertEqual(data["goods"][0]["usage"], self.good_on_licence.usage)
