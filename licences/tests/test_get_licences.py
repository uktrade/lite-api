from django.urls import reverse
from rest_framework import status

from api.applications.models import CountryOnApplication
from cases.enums import CaseTypeEnum, AdviceType, CaseTypeSubTypeEnum
from cases.models import CaseType
from cases.tests.factories import FinalAdviceFactory, GoodCountryDecisionFactory
from licences.enums import LicenceStatus
from licences.models import Licence
from licences.tests.factories import GoodOnLicenceFactory
from licences.views.main import LicenceType
from api.open_general_licences.tests.factories import OpenGeneralLicenceCaseFactory, OpenGeneralLicenceFactory
from static.countries.models import Country
from static.statuses.enums import CaseStatusEnum
from static.statuses.models import CaseStatus
from test_helpers.clients import DataTestClient
from test_helpers.helpers import node_by_id


class GetLicencesTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.url = reverse("licences:licences")
        self.standard_application = self.create_standard_application_case(self.organisation)
        self.f680_application = self.create_mod_clearance_application_case(self.organisation, CaseTypeEnum.F680)
        self.gifting_application = self.create_mod_clearance_application_case(self.organisation, CaseTypeEnum.GIFTING)
        self.exhibition_application = self.create_mod_clearance_application_case(
            self.organisation, CaseTypeEnum.EXHIBITION
        )
        self.open_application = self.create_open_application_case(self.organisation)
        self.open_application.goods_type.first().countries.set([Country.objects.first()])
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
            application: self.create_licence(application, status=LicenceStatus.ISSUED)
            for application in self.applications
        }

        for application, licence in self.licences.items():
            for good in application.goods.all():
                FinalAdviceFactory(user=self.gov_user, good=good.good, case=application)
                GoodOnLicenceFactory(licence=licence, good=good, quantity=good.quantity, value=good.value)
            for goods_type in application.goods_type.all():
                FinalAdviceFactory(user=self.gov_user, goods_type=goods_type, case=application)
                for country in goods_type.countries.all():
                    FinalAdviceFactory(user=self.gov_user, country=country, case=application)
                    GoodCountryDecisionFactory(case=application, goods_type=goods_type, country=country)

    def test_get_all_licences(self):
        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()["results"]
        response_data.reverse()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), len(self.applications))
        for i in range(len(self.applications)):
            licence = response_data[i]
            licence_object = list(self.licences.values())[i]
            self.assertEqual(licence["id"], str(licence_object.id))
            self.assertEqual(licence["application"]["id"], str(self.applications[i].id))
            self.assertEqual(licence["reference_code"], licence_object.reference_code)
            self.assertEqual(licence["status"]["key"], licence_object.status)
            self.assertEqual(licence["application"]["documents"][0]["id"], str(self.documents[i].id))
        # Assert correct information is returned
        for licence in self.licences.values():
            licence_data = node_by_id(response_data, licence.id)

            if licence.case.case_type.sub_type == CaseTypeSubTypeEnum.OPEN:
                good = licence.case.goods_type.first()
                destination = good.countries.first()

                self.assertEqual(licence_data["goods"][0]["description"], good.description)
                self.assertEqual(
                    licence_data["goods"][0]["control_list_entries"][0]["text"],
                    good.control_list_entries.all()[0].text,
                )
                self.assertEqual(licence_data["application"]["destinations"][0]["country"]["id"], destination.id)
            else:
                if licence.case.case_type.sub_type != CaseTypeSubTypeEnum.EXHIBITION:
                    destination = licence.case.end_user.party
                    self.assertEqual(
                        licence_data["application"]["destinations"][0]["country"]["id"], destination.country_id,
                    )

                good_on_application = licence.case.goods.first()

                self.assertEqual(
                    licence_data["goods"][0]["good_on_application_id"], str(good_on_application.id),
                )
                self.assertEqual(
                    licence_data["goods"][0]["control_list_entries"][0]["rating"],
                    good_on_application.good.control_list_entries.all()[0].rating,
                )

    def test_get_standard_licences_only(self):
        response = self.client.get(self.url + "?licence_type=" + LicenceType.LICENCE, **self.exporter_headers)
        response_data = response.json()["results"]
        ids = [licence["id"] for licence in response_data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 2)
        self.assertTrue(str(self.licences[self.standard_application].id) in ids)
        self.assertTrue(str(self.licences[self.open_application].id) in ids)

    def test_get_clearance_licences_only(self):
        response = self.client.get(self.url + "?licence_type=" + LicenceType.CLEARANCE, **self.exporter_headers)
        response_data = response.json()["results"]
        ids = [licence["id"] for licence in response_data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 3)
        self.assertTrue(str(self.licences[self.exhibition_application].id) in ids)
        self.assertTrue(str(self.licences[self.f680_application].id) in ids)
        self.assertTrue(str(self.licences[self.gifting_application].id) in ids)

    def test_draft_licences_are_not_included(self):
        draft_licence = self.create_licence(self.standard_application, status=LicenceStatus.DRAFT)

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(str(draft_licence.id) not in [licence["id"] for licence in response_data])

    def test_ogel_licences_are_not_included(self):
        open_general_licence = OpenGeneralLicenceFactory(case_type=CaseType.objects.get(id=CaseTypeEnum.OGEL.id))
        open_general_licence_case = OpenGeneralLicenceCaseFactory(
            open_general_licence=open_general_licence,
            site=self.organisation.primary_site,
            organisation=self.organisation,
        )
        ogel_licence = Licence.objects.get(case=open_general_licence_case)

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(str(ogel_licence.id) not in [licence["id"] for licence in response_data])


class GetLicencesFilterTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.url = reverse("licences:licences")
        self.standard_application = self.create_standard_application_case(self.organisation)
        self.open_application = self.create_open_application_case(self.organisation)
        self.standard_application_licence = self.create_licence(self.standard_application, status=LicenceStatus.ISSUED)
        self.open_application_licence = self.create_licence(self.open_application, status=LicenceStatus.ISSUED)

    def test_only_my_organisations_licences_are_returned(self):
        self.standard_application.organisation = self.create_organisation_with_exporter_user()[0]
        self.standard_application.save()

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], str(self.open_application_licence.id))

    def test_draft_licences_ignored(self):
        self.open_application_licence.status = LicenceStatus.DRAFT
        self.open_application_licence.save()

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], str(self.standard_application_licence.id))

    def test_filter_by_application_name(self):
        response = self.client.get(self.url + "?reference=" + self.standard_application.name, **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], str(self.standard_application_licence.id))

    def test_filter_by_ecju_reference(self):
        response = self.client.get(
            self.url + "?reference=" + self.standard_application.reference_code, **self.exporter_headers
        )
        response_data = response.json()["results"]

        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], str(self.standard_application_licence.id))

    def test_filter_by_control_list_entry(self):
        response = self.client.get(self.url + "?clc=ML1a", **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(len(response_data), 2)
        self.assertIn(str(self.standard_application_licence.id), str(response_data))
        self.assertIn(str(self.open_application_licence.id), str(response_data))

    def test_filter_by_country_standard_application(self):
        country = Country.objects.first()
        end_user = self.standard_application.end_user.party
        end_user.country = country
        end_user.save()

        response = self.client.get(self.url + "?country=" + str(country.id), **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], str(self.standard_application_licence.id))

    def test_filter_by_country_open_application(self):
        country = Country.objects.first()
        country_on_app = CountryOnApplication.objects.get(application=self.open_application)
        country_on_app.country = country
        country_on_app.save()

        response = self.client.get(self.url + "?country=" + str(country.id), **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], str(self.open_application_licence.id))

    def test_filter_by_end_user_standard_application(self):
        # End user filter is N/A for open applications
        end_user_name = self.standard_application.end_user.party.name

        response = self.client.get(self.url + "?end_user=" + end_user_name, **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], str(self.standard_application_licence.id))

    def test_filter_by_active_only(self):
        self.standard_application.status = CaseStatus.objects.get(status=CaseStatusEnum.SURRENDERED)
        self.standard_application.save()

        response = self.client.get(self.url + "?active_only=True", **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], str(self.open_application_licence.id))
