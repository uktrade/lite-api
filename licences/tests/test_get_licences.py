from django.urls import reverse
from rest_framework import status

from cases.enums import CaseTypeEnum, AdviceType
from test_helpers.clients import DataTestClient


class GetLicencesTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.url = reverse("licences:licences")
        self.standard_application = self.create_standard_application_case(self.organisation)
        self.f680_application = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.F680)
        self.gifting_application = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.F680)
        self.exhibition_application = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.F680)
        self.open_application = self.create_open_application_case(self.organisation)
        self.applications = [
            self.standard_application,
            self.f680_application,
            self.gifting_application,
            self.exhibition_application,
            self.open_application,
        ]
        self.template = self.create_letter_template(
            case_types=[
                CaseTypeEnum.SIEL.id,
                CaseTypeEnum.F680.id,
                CaseTypeEnum.GIFTING.id,
                CaseTypeEnum.EXHIBITION.id,
                CaseTypeEnum.OIEL.id,
            ]
        )
        self.documents = [
            self.create_generated_case_document(application, self.template, advice_type=AdviceType.APPROVE)
            for application in self.applications
        ]
        self.licences = [self.create_licence(application, is_complete=True) for application in self.applications]

    def test_get_all_licences(self):
        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for i in range(len(self.applications)):
            licence = response_data[i]
            self.assertEqual(licence["id"], str(self.licences[i].id))
            self.assertEqual(licence["application"]["id"], str(self.applications[i].id))
            self.assertEqual(licence["application"]["reference_code"], self.applications[i].reference_code)
            self.assertEqual(licence["application"]["status"]["id"], str(self.applications[i].status_id))
            self.assertEqual(licence["application"]["documents"][0]["id"], str(self.documents[i].id))

        # Standard Applications
        for i in range(len(self.applications) - 1):
            licence = response_data[i]
            destination = self.standard_application.end_user.party
            good = self.standard_application.goods.first().good
            good_on_app = good.goods_on_application.first()
            self.assertEqual(licence["application"]["destinations"][0]["name"], destination.name)
            self.assertEqual(
                licence["application"]["destinations"][0]["country"]["id"], destination.country_id,
            )
            self.assertEqual(
                licence["application"]["goods"][0]["good"]["description"], good.description,
            )
            self.assertEqual(
                licence["application"]["goods"][0]["quantity"], good_on_app.quantity,
            )
            self.assertEqual(
                licence["application"]["goods"][0]["good"]["control_code"], good.control_code,
            )

        # Open Application
        licence = response_data[-1]
        destination = self.open_application.application_countries.first()
        good = self.open_application.goods_type.first()
        self.assertEqual(licence["application"]["goods"][0]["description"], good.description)
        self.assertEqual(licence["application"]["goods"][0]["control_code"], good.control_code)
        self.assertEqual(licence["application"]["destinations"][0]["country"]["id"], destination.country_id)
