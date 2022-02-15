import mohawk

from django.conf import settings
from django.urls import reverse
from django.test import override_settings
from rest_framework import status
from urllib import parse

from api.cases.enums import CaseTypeEnum
from api.cases.models import CaseType
from api.core.requests import get_hawk_sender
from api.licences.enums import LicenceStatus
from api.open_general_licences.tests.factories import OpenGeneralLicenceFactory, OpenGeneralLicenceCaseFactory
from api.organisations.tests.factories import SiteFactory
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class InternalListTests(DataTestClient):
    def setUp(self):
        super().setUp()
        case_type = CaseType.objects.get(id=CaseTypeEnum.OGTCL.id)
        self.ogl_1 = OpenGeneralLicenceFactory(name="b", case_type=case_type)
        self.ogl_2 = OpenGeneralLicenceFactory(name="c", case_type=case_type)
        self.url = reverse("open_general_licences:list")
        self.gov_user.role = self.super_user_role
        self.gov_user.save()

    def test_get_list_back(self):
        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()["results"]

        self.assertEqual(str(self.ogl_1.id), response_data[0]["id"])
        self.assertEqual(str(self.ogl_2.id), response_data[1]["id"])

    def test_get_list_back_alphabetical(self):
        self.ogl_2.name = "a"
        self.ogl_2.save()

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()["results"]

        self.assertEqual(str(self.ogl_2.id), response_data[0]["id"])
        self.assertEqual(str(self.ogl_1.id), response_data[1]["id"])

    def test_fail_without_permission(self):
        self.gov_user.role = self.default_role
        self.gov_user.save()

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ExporterListTests(DataTestClient):
    def setUp(self):
        super().setUp()
        case_type = CaseType.objects.get(id=CaseTypeEnum.OGTCL.id)
        self.open_general_licence = OpenGeneralLicenceFactory(name="b", case_type=case_type)
        self.url = reverse("open_general_licences:list")
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
        self.site = SiteFactory(organisation=self.organisation)
        self.open_general_licence_case = OpenGeneralLicenceCaseFactory(
            open_general_licence=self.open_general_licence,
            site=self.organisation.primary_site,
            organisation=self.organisation,
        )
        self.open_general_licence_case_2 = OpenGeneralLicenceCaseFactory(
            open_general_licence=self.open_general_licence,
            site=self.site,
            organisation=self.organisation,
        )

    def test_exporter_view_licences_success(self):
        response = self.client.get(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 1)
        self.assertEqual(len(response.json()["results"][0]["registrations"]), 2)
        registration = response.json()["results"][0]["registrations"][0]
        self.assertEqual(registration["reference_code"], self.open_general_licence_case.reference_code)
        self.assertEqual(registration["site"]["id"], str(self.organisation.primary_site.id))
        self.assertEqual(registration["site"]["name"], self.organisation.primary_site.name)
        self.assertEqual(
            registration["site"]["address"]["address_line_1"], self.organisation.primary_site.address.address_line_1
        )
        self.assertEqual(
            registration["site"]["address"]["address_line_2"], self.organisation.primary_site.address.address_line_2
        )
        self.assertEqual(registration["site"]["address"]["city"], self.organisation.primary_site.address.city)
        self.assertEqual(
            registration["site"]["address"]["country"]["name"], self.organisation.primary_site.address.country.name
        )
        self.assertEqual(registration["site"]["address"]["postcode"], self.organisation.primary_site.address.postcode)
        self.assertEqual(registration["site"]["address"]["region"], self.organisation.primary_site.address.region)
        self.assertEqual(
            registration["site"]["records_located_at"]["name"],
            self.organisation.primary_site.site_records_located_at.name,
        )
        self.assertEqual(registration["status"]["key"], LicenceStatus.ISSUED)
        self.assertEqual(registration["submitted_at"], self.open_general_licence_case.submitted_at)

    def test_exporter_view_site_licences_success(self):
        response = self.client.get(
            self.url + "?site=" + str(self.organisation.primary_site.id), **self.exporter_headers
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 1)
        self.assertEqual(len(response.json()["results"][0]["registrations"]), 2)

    def test_exporter_view_active_licences_success(self):
        self.open_general_licence_case_2.status = get_case_status_by_status(CaseStatusEnum.DRAFT)
        self.open_general_licence_case_2.save()
        response = self.client.get(self.url + "?active_only=True", **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 1)
        self.assertEqual(len(response.json()["results"][0]["registrations"]), 1)

    def test_exporter_view_registered_licences_success(self):
        response = self.client.get(self.url + "?registered=True", **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 1)
        self.assertEqual(len(response.json()["results"][0]["registrations"]), 2)
