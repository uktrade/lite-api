from django.urls import reverse
from rest_framework import status

from cases.enums import CaseTypeEnum, AdviceType
from test_helpers.clients import DataTestClient


class GetNLRsTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.url = reverse("licences:nlrs")
        self.standard_application = self.create_standard_application_case(self.organisation)
        self.f680_application = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.F680)
        self.gifting_application = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.GIFTING)
        self.exhibition_application = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.EXHIBITION)
        self.applications = [
            self.standard_application,
            self.f680_application,
            self.gifting_application,
            self.exhibition_application,
        ]
        self.template = self.create_letter_template(
            case_types=[
                CaseTypeEnum.SIEL.id,
                CaseTypeEnum.F680.id,
                CaseTypeEnum.GIFTING.id,
                CaseTypeEnum.EXHIBITION.id,
            ]
        )
        self.documents = [
            self.create_generated_case_document(application, self.template, advice_type=AdviceType.NO_LICENCE_REQUIRED)
            for application in self.applications
        ]

    def test_get_all_nlrs(self):
        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()["results"]
        response_data.reverse()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), len(self.applications))
        for application in self.applications:
            match = False
            for nlr in response_data:
                if nlr["case_id"] == str(application.id):
                    document = nlr
                    self.assertEqual(document["case_id"], str(application.id))
                    self.assertEqual(document["case_reference"], application.reference_code)
                    self.assertEqual(document["advice_type"], "no_licence_required")
                    match = True
                    break

            self.assertTrue(match)
