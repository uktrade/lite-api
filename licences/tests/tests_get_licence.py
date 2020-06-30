from decimal import Decimal

from django.urls import reverse
from django.utils import timezone

from applications.tests.factories import StandardApplicationFactory, GoodOnApplicationFactory
from cases.enums import AdviceType
from cases.tests.factories import FinalAdviceFactory
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
            status=LicenceStatus.ISSUED.value,
            duration=100,
        )
        self.url = reverse("cases:licences", kwargs={"pk": self.application.id})

    def test_get_licence(self):
        good_1 = GoodFactory(organisation=self.application.organisation)
        good_1_advice = FinalAdviceFactory(
            user=self.gov_user, team=self.team, case=self.application, good=good_1, type=AdviceType.APPROVE
        )
        good_on_application_1 = GoodOnApplicationFactory(
            application=self.application, good=good_1, quantity=100.0, value=Decimal("1000.00")
        )
        good_2 = GoodFactory(organisation=self.application.organisation)
        good_2_advice = FinalAdviceFactory(
            user=self.gov_user, team=self.team, case=self.application, good=good_2, type=AdviceType.APPROVE
        )
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
            licence=self.licence,
        )
        good_2_on_licence_1 = GoodOnLicenceFactory(
            good=good_on_application_2, quantity=good_on_application_2.quantity, usage=50.0, licence=self.licence
        )
        good_2_on_licence_2 = GoodOnLicenceFactory(
            good=good_on_application_2,
            quantity=good_on_application_2.quantity - good_2_on_licence_1.quantity,
            usage=30.0,
            licence=self.licence,
        )

        data = self.client.get(self.url, **self.gov_headers).json()

        self.assertEqual(
            data["licence"],
            {
                "id": str(self.licence.id),
                "start_date": str(self.licence.start_date),
                "status": self.licence.status,
                "duration": self.licence.duration,
            },
        )
        self.assertEqual(
            sorted(data["goods"], key=lambda x: x["id"]),
            sorted(
                [
                    {
                        "advice": {
                            "type": AdviceType.as_representation(good_1_advice.type),
                            "text": good_1_advice.text,
                            "proviso": good_1_advice.proviso,
                        },
                        "control_list_entries": [],
                        "description": good_1.description,
                        "unit": None,
                        "good_id": str(good_on_application_1.good.id),
                        "id": str(good_on_application_1.id),
                        "licenced_value": float(good_1_on_licence_1.quantity) * float(good_on_application_1.value),
                        "usage": good_1_on_licence_1.usage + good_1_on_licence_2.usage,
                        "usage_licenced": good_1_on_licence_1.quantity,
                        "usage_applied_for": good_on_application_1.quantity,
                        "value": str(good_on_application_1.value),
                    },
                    {
                        "advice": {
                            "type": AdviceType.as_representation(good_2_advice.type),
                            "text": good_2_advice.text,
                            "proviso": good_2_advice.proviso,
                        },
                        "control_list_entries": [],
                        "description": good_2.description,
                        "unit": None,
                        "good_id": str(good_on_application_2.good.id),
                        "id": str(good_on_application_2.id),
                        "licenced_value": float(good_2_on_licence_1.quantity) * float(good_on_application_2.value),
                        "usage": good_2_on_licence_1.usage + good_2_on_licence_2.usage,
                        "usage_licenced": good_2_on_licence_1.quantity,
                        "usage_applied_for": good_on_application_2.quantity,
                        "value": str(good_on_application_2.value),
                    },
                ],
                key=lambda x: x["id"],
            ),
        )
