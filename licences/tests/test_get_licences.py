from django.urls import reverse
from rest_framework import status

from cases.enums import CaseTypeEnum, AdviceType
from licences.views import LicenceType
from static.decisions.models import Decision
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
        self.licences = {
            application: self.create_licence(application, is_complete=True) for application in self.applications
        }

    def test_get_all_licences(self):
        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), len(self.applications))
        for i in range(len(self.applications)):
            licence = response_data[i]
            self.assertEqual(licence["id"], str(list(self.licences.values())[i].id))
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

    def test_get_standard_licences_only(self):
        response = self.client.get(self.url + "?type=" + LicenceType.LICENCE, **self.exporter_headers)
        response_data = response.json()["results"]
        ids = [licence["id"] for licence in response_data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 2)
        self.assertTrue(str(self.licences[self.standard_application].id) in ids)
        self.assertTrue(str(self.licences[self.open_application].id) in ids)

    def test_get_clearance_licences_only(self):
        response = self.client.get(self.url + "?type=" + LicenceType.CLEARANCE, **self.exporter_headers)
        response_data = response.json()["results"]
        ids = [licence["id"] for licence in response_data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 3)
        self.assertTrue(str(self.licences[self.exhibition_application].id) in ids)
        self.assertTrue(str(self.licences[self.f680_application].id) in ids)
        self.assertTrue(str(self.licences[self.gifting_application].id) in ids)

    def test_get_nlr_licences_only(self):
        self.licences[self.standard_application].decisions.set(
            [Decision.objects.get(name=AdviceType.NO_LICENCE_REQUIRED)]
        )

        response = self.client.get(self.url + "?type=" + LicenceType.NLR, **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(str(self.licences[self.standard_application].id), response_data[0]["id"])


class GetLicencesFilterTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.url = reverse("licences:licences")
        self.standard_application = self.create_standard_application_case(self.organisation)
        self.open_application = self.create_open_application_case(self.organisation)
        self.standard_application_licence = self.create_licence(self.standard_application, is_complete=True)
        self.open_application_licence = self.create_licence(self.open_application, is_complete=True)

    def test_only_my_organisations_licences_are_returned(self):
        self.standard_application.organisation = self.create_organisation_with_exporter_user()[0]
        self.standard_application.save()

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], str(self.open_application_licence.id))

    def test_incomplete_licences_ignored(self):
        self.open_application_licence.is_complete = False
        self.open_application_licence.save()

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], str(self.standard_application_licence.id))

    def test_filter_by_reference(self):
        response = self.client.get(self.url + "?reference=GBSIEL/2020/0000001/P", **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], str(self.standard_application_licence.id))

    def test_filter_by_clc_standard_application(self):
        good = self.standard_application.goods.first().good
        good.control_code = "ML1a"
        good.save()

        response = self.client.get(self.url + "?clc=ML1a", **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], str(self.standard_application_licence.id))

    def test_filter_by_clc_open_application(self):
        good = self.open_application.goods_type.first()
        good.control_code = "ML1b"
        good.save()

        response = self.client.get(self.url + "?clc=ML1b", **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], str(self.open_application_licence.id))
