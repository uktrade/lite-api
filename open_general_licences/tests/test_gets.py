from django.urls import reverse
from rest_framework import status

from cases.enums import CaseTypeEnum
from cases.models import CaseType
from open_general_licences.tests.factories import OpenGeneralLicenceFactory, OpenGeneralLicenceCaseFactory
from organisations.tests.factories import SiteFactory
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient
from test_helpers.helpers import generate_key_value_pair


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

        self.assertEquals(response.status_code, status.HTTP_200_OK)

        response_data = response.json()["results"]

        self.assertEqual(str(self.ogl_1.id), response_data[0]["id"])
        self.assertEqual(str(self.ogl_2.id), response_data[1]["id"])

    def test_get_list_back_alphabetical(self):
        self.ogl_2.name = "a"
        self.ogl_2.save()

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEquals(response.status_code, status.HTTP_200_OK)

        response_data = response.json()["results"]

        self.assertEqual(str(self.ogl_2.id), response_data[0]["id"])
        self.assertEqual(str(self.ogl_1.id), response_data[1]["id"])

    def test_fail_without_permission(self):
        self.gov_user.role = self.default_role
        self.gov_user.save()

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)


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
            open_general_licence=self.open_general_licence, site=self.site, organisation=self.organisation,
        )

    def test_exporter_view_licences_success(self):
        response = self.client.get(self.url, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.json()["results"]), 1)
        self.assertEquals(len(response.json()["results"][0]["registrations"]), 2)
        self.assertIn(
            {
                "reference_code": self.open_general_licence_case.reference_code,
                "site": {
                    "address": {
                        "address_line_1": self.organisation.primary_site.address.address_line_1,
                        "address_line_2": self.organisation.primary_site.address.address_line_2,
                        "city": self.organisation.primary_site.address.city,
                        "country": {"name": "United Kingdom"},
                        "postcode": self.organisation.primary_site.address.postcode,
                        "region": self.organisation.primary_site.address.region,
                    },
                    "id": str(self.organisation.primary_site.id),
                    "name": self.organisation.primary_site.name,
                    "records_located_at": {"name": self.organisation.primary_site.site_records_located_at.name},
                },
                "status": generate_key_value_pair(self.open_general_licence_case.status.status, CaseStatusEnum.choices),
                "submitted_at": self.open_general_licence_case.submitted_at,
            },
            response.json()["results"][0]["registrations"],
        )

    def test_exporter_view_site_licences_success(self):
        response = self.client.get(
            self.url + "?site=" + str(self.organisation.primary_site.id), **self.exporter_headers
        )

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.json()["results"]), 1)
        self.assertEquals(len(response.json()["results"][0]["registrations"]), 2)

    def test_exporter_view_active_licences_success(self):
        self.open_general_licence_case_2.status = get_case_status_by_status(CaseStatusEnum.DRAFT)
        self.open_general_licence_case_2.save()
        response = self.client.get(self.url + "?active_only=True", **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.json()["results"]), 1)
        self.assertEquals(len(response.json()["results"][0]["registrations"]), 1)

    def test_exporter_view_registered_licences_success(self):
        response = self.client.get(self.url + "?registered=True", **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.json()["results"]), 1)
        self.assertEquals(len(response.json()["results"][0]["registrations"]), 2)
