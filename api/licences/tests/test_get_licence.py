from django.urls import reverse
from rest_framework import status

from api.applications.tests.factories import StandardApplicationFactory, GoodOnApplicationFactory
from api.cases.enums import AdviceType, CaseTypeEnum
from api.cases.tests.factories import FinalAdviceFactory
from api.goods.tests.factories import GoodFactory
from api.licences.enums import LicenceStatus
from api.licences.tests.factories import StandardLicenceFactory, GoodOnLicenceFactory
from api.staticdata.units.enums import Units
from test_helpers.clients import DataTestClient


class GetLicenceTests(DataTestClient):
    def test_get_licence_gov_view(self):
        application = StandardApplicationFactory()
        licence = StandardLicenceFactory(case=application, status=LicenceStatus.ISSUED)
        self.url = reverse("cases:licences", kwargs={"pk": application.id})

        good = GoodFactory(organisation=application.organisation)
        good_advice = FinalAdviceFactory(
            user=self.gov_user, team=self.team, case=application, good=good, type=AdviceType.APPROVE
        )
        good_on_application = GoodOnApplicationFactory(
            application=application, good=good, quantity=100.0, value=1500, unit=Units.KGM
        )
        good_on_licence = GoodOnLicenceFactory(
            good=good_on_application,
            quantity=good_on_application.quantity,
            usage=20.0,
            value=good_on_application.value,
            licence=licence,
        )

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()["licence"]

        self.assertEqual(response_data["id"], str(licence.id))
        self.assertEqual(response_data["start_date"], licence.start_date.strftime("%Y-%m-%d"))
        self.assertEqual(response_data["duration"], licence.duration)
        self.assertEqual(response_data["goods_on_licence"][0]["good_on_application_id"], str(good_on_application.id))
        self.assertEqual(response_data["goods_on_licence"][0]["usage"], good_on_licence.usage)
        self.assertEqual(response_data["goods_on_licence"][0]["name"], good.name)
        self.assertEqual(response_data["goods_on_licence"][0]["description"], good.description)
        self.assertEqual(
            response_data["goods_on_licence"][0]["is_good_controlled"],
            good_on_application.is_good_controlled,
        )
        self.assertEqual(response_data["goods_on_licence"][0]["units"]["key"], good_on_application.unit)
        self.assertEqual(response_data["goods_on_licence"][0]["applied_for_quantity"], good_on_application.quantity)
        self.assertEqual(response_data["goods_on_licence"][0]["applied_for_value"], good_on_application.value)
        self.assertEqual(response_data["goods_on_licence"][0]["licenced_quantity"], good_on_licence.quantity)
        self.assertEqual(response_data["goods_on_licence"][0]["licenced_value"], good_on_licence.value)
        self.assertEqual(
            response_data["goods_on_licence"][0]["applied_for_value_per_item"],
            good_on_application.value / good_on_application.quantity,
        )
        self.assertEqual(
            response_data["goods_on_licence"][0]["licenced_value_per_item"],
            good_on_licence.value / good_on_licence.quantity,
        )
        self.assertEqual(
            len(response_data["goods_on_licence"][0]["control_list_entries"]), good.control_list_entries.count()
        )
        self.assertEqual(response_data["goods_on_licence"][0]["advice"]["type"]["key"], good_advice.type)
        self.assertEqual(response_data["goods_on_licence"][0]["advice"]["text"], good_advice.text)
        self.assertEqual(response_data["goods_on_licence"][0]["advice"]["proviso"], good_advice.proviso)

    def test_get_licence_exporter_view(self):
        application = self.create_standard_application_case(self.organisation)

        template = self.create_letter_template(
            case_types=[
                CaseTypeEnum.SIEL.id,
            ]
        )

        licence = StandardLicenceFactory(case=application, status=LicenceStatus.ISSUED)
        document = self.create_generated_case_document(application, template, licence=licence)

        good = GoodFactory(
            is_good_controlled=True,
            organisation=application.organisation,
            control_list_entries=["ML1a", "ML2b"],
        )
        good_on_application = GoodOnApplicationFactory(
            application=application,
            control_list_entries=["ML5a", "ML5b"],
            good=good,
            quantity=100.0,
            value=1500,
            unit=Units.KGM,
        )
        good_on_licence = GoodOnLicenceFactory(
            good=good_on_application,
            quantity=good_on_application.quantity,
            usage=20.0,
            value=good_on_application.value,
            licence=licence,
        )

        url = reverse("licences:licence", kwargs={"pk": str(licence.id)})
        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["application"]["id"], str(application.id))
        self.assertEqual(
            response_data["application"]["case_type"],
            {
                "sub_type": {
                    "key": "standard",
                    "value": "Standard Licence",
                },
            },
        )
        self.assertEqual(response_data["document"], {"id": str(document.id)})
        self.assertEqual(response_data["duration"], licence.duration)
        self.assertEqual(
            response_data["goods"],
            [
                {
                    "applied_for_quantity": 100.0,
                    "assessed_control_list_entries": [
                        {
                            "id": str(cle.pk),
                            "rating": cle.rating,
                            "text": cle.text,
                        }
                        for cle in good_on_application.control_list_entries.all()
                    ],
                    "control_list_entries": [
                        {
                            "id": str(cle.pk),
                            "rating": cle.rating,
                            "text": cle.text,
                        }
                        for cle in good.control_list_entries.all()
                    ],
                    "description": good.description,
                    "id": str(good_on_licence.id),
                    "licenced_quantity": good_on_licence.quantity,
                    "licenced_value": good_on_licence.value,
                    "name": good.name,
                    "units": {"key": "KGM", "value": "Kilograms"},
                    "usage": good_on_licence.usage,
                }
            ],
        )
        self.assertEqual(response_data["id"], str(licence.pk))
        self.assertEqual(response_data["reference_code"], licence.reference_code)
        self.assertEqual(response_data["start_date"], licence.start_date.strftime("%Y-%m-%d"))
        self.assertEqual(response_data["status"], {"key": "issued", "value": "Issued"})
