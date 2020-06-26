from decimal import Decimal

from django.urls import reverse
from django.utils import timezone

from applications.tests.factories import StandardApplicationFactory, GoodOnApplicationFactory
from goods.tests.factories import GoodFactory
from licences.enums import LicenceStatus
from licences.tests.factories import LicenceFactory, GoodOnLicenceFactory
from test_helpers.clients import DataTestClient


class GetLicencesTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.application = StandardApplicationFactory()
        self.licence = LicenceFactory(
            application=self.application,
            start_date=timezone.now().date(),
            status=LicenceStatus.REVOKED,
            duration=100,
        )
        self.url = reverse("cases:licences", kwargs={"pk": self.application.id})

    def test_reissue_licence(self):
        good_1 = GoodFactory(organisation=self.application.organisation)
        good_on_application_1 = GoodOnApplicationFactory(
            application=self.application, good=good_1, quantity=100.0, value=Decimal("1000.00")
        )
        good_2 = GoodFactory(organisation=self.application.organisation)
        good_on_application_2 = GoodOnApplicationFactory(
            application=self.application, good=good_2, quantity=150.0, value=Decimal("1500.00")
        )
        good_1_on_licence_1 = GoodOnLicenceFactory(
            good=good_on_application_1, quantity=good_on_application_1.quantity, usage=20.0, licence=self.licence
        )
        good_1_on_licence_2 = GoodOnLicenceFactory(
            good=good_on_application_1,
            quantity=good_on_application_1.quantity - good_1_on_licence_1.quantity,
            usage=10.0,
            licence=self.licence
        )
        good_2_on_licence_1 = GoodOnLicenceFactory(
            good=good_on_application_2, quantity=good_on_application_2.quantity, usage=50.0, licence=self.licence
        )
        good_2_on_licence_2 = GoodOnLicenceFactory(
            good=good_on_application_2,
            quantity=good_on_application_2.quantity - good_2_on_licence_1.quantity,
            usage=30.0,
            licence=self.licence
        )

        data = self.client.get(self.url, **self.gov_headers).json()

        self.assertEqual(
            data["licence"],
            {
                'id': str(self.licence.id),
                'start_date': str(self.licence.start_date),
                'status': self.licence.status.value,
                'duration': self.licence.duration,
                'reissued': True
            }
        )
        self.assertEqual(
            sorted(data["goods"], key=lambda x: x["id"]),
            sorted(
                [
                    {
                        'advice': {'proviso': None, 'text': None, 'type': None},
                        'control_list_entries': [],
                        'unit': None,
                        'id': str(good_on_application_1.id),
                        'usage_total': good_1_on_licence_1.usage + good_1_on_licence_2.usage,
                        'usage_licenced': good_1_on_licence_1.quantity,
                        'usage_applied_for': good_on_application_1.quantity,
                        'value': str(good_on_application_1.value)
                    },
                    {
                        'advice': {'proviso': None, 'text': None, 'type': None},
                        'control_list_entries': [],
                        'unit': None,
                        'id': str(good_on_application_2.id),
                        'usage_total': good_2_on_licence_1.usage + good_2_on_licence_2.usage,
                        'usage_licenced': good_2_on_licence_1.quantity,
                        'usage_applied_for': good_on_application_2.quantity,
                        'value': str(good_on_application_2.value)
                    }
                ],
                key=lambda x: x["id"]
            )
        )
