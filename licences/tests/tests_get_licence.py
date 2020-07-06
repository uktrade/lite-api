from decimal import Decimal

from django.urls import reverse
from django.utils import timezone

from applications.tests.factories import StandardApplicationFactory, GoodOnApplicationFactory
from cases.enums import AdviceType
from cases.tests.factories import FinalAdviceFactory
from goods.tests.factories import GoodFactory
from licences.enums import LicenceStatus
from licences.tests.factories import LicenceFactory, GoodOnLicenceFactory
from static.units.enums import Units
from test_helpers.clients import DataTestClient


class GetLicencesTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.application = StandardApplicationFactory()
        self.licence = LicenceFactory(
            application=self.application, start_date=timezone.now().date(), status=LicenceStatus.ISSUED, duration=100,
        )
        self.url = reverse("cases:licences", kwargs={"pk": self.application.id})

    def test_get_licence_gov_view(self):
        good = GoodFactory(organisation=self.application.organisation)
        good_advice = FinalAdviceFactory(
            user=self.gov_user, team=self.team, case=self.application, good=good, type=AdviceType.APPROVE
        )
        good_on_application = GoodOnApplicationFactory(
            application=self.application, good=good, quantity=100.0, value=1500, unit=Units.KGM
        )
        good_on_licence = GoodOnLicenceFactory(
            good=good_on_application, quantity=good_on_application.quantity, usage=20.0, value=good_on_application.value, licence=self.licence
        )

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()["licence"]

        self.assertEqual(response_data["id"], str(self.licence.id))
        self.assertEqual(response_data["start_date"], self.licence.start_date.strftime("%Y-%m-%d"))
        self.assertEqual(response_data["duration"], self.licence.duration)
        self.assertEqual(response_data["goods_on_licence"][0]["good_on_application_id"], str(good_on_application.id))
        self.assertEqual(response_data["goods_on_licence"][0]["usage"], good_on_licence.usage)
        self.assertEqual(response_data["goods_on_licence"][0]["description"], good.description)
        self.assertEqual(response_data["goods_on_licence"][0]["units"]["key"], good_on_application.unit)
        self.assertEqual(response_data["goods_on_licence"][0]["applied_for_quantity"], good_on_application.quantity)
        self.assertEqual(response_data["goods_on_licence"][0]["applied_for_value"], good_on_application.value)
        self.assertEqual(response_data["goods_on_licence"][0]["licenced_quantity"], good_on_licence.quantity)
        self.assertEqual(response_data["goods_on_licence"][0]["licenced_value"], good_on_licence.value)
        self.assertEqual(response_data["goods_on_licence"][0]["applied_for_value_per_item"], good_on_application.value / good_on_application.quantity)
        self.assertEqual(response_data["goods_on_licence"][0]["licenced_value_per_item"], good_on_licence.value / good_on_licence.quantity)
        self.assertEqual(len(response_data["goods_on_licence"][0]["control_list_entries"]), good.control_list_entries.count())
        self.assertEqual(response_data["goods_on_licence"][0]["advice"]["type"]["key"], good_advice.type)
        self.assertEqual(response_data["goods_on_licence"][0]["advice"]["text"], good_advice.text)
        self.assertEqual(response_data["goods_on_licence"][0]["advice"]["proviso"], good_advice.proviso)
