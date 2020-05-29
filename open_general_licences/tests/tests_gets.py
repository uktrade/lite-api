from django.urls import reverse
from rest_framework import status

from cases.enums import CaseTypeEnum
from cases.models import CaseType
from open_general_licences.tests.factories import OpenGeneralLicenceFactory
from test_helpers.clients import DataTestClient


class test_get_list(DataTestClient):
    def setUp(self):
        super().setUp()
        case_type = CaseType.objects.get(id=CaseTypeEnum.OGTCL.id)
        self.ogl_1 = OpenGeneralLicenceFactory(name="b", case_type=case_type)
        self.ogl_2 = OpenGeneralLicenceFactory(name="c", case_type=case_type)
        self.URL = reverse("open_general_licences:list")
        self.gov_user.role = self.super_user_role
        self.gov_user.save()

    def test_get_list_back(self):
        response = self.client.get(self.URL, **self.gov_headers)

        self.assertEquals(response.status_code, status.HTTP_200_OK)

        response_data = response.json()["results"]

        self.assertEqual(str(self.ogl_1.id), response_data[0]["id"])
        self.assertEqual(str(self.ogl_2.id), response_data[1]["id"])

    def test_get_list_back_alphabetical(self):
        self.ogl_2.name = "a"
        self.ogl_2.save()

        response = self.client.get(self.URL, **self.gov_headers)

        self.assertEquals(response.status_code, status.HTTP_200_OK)

        response_data = response.json()["results"]

        self.assertEqual(str(self.ogl_2.id), response_data[0]["id"])
        self.assertEqual(str(self.ogl_1.id), response_data[1]["id"])

    def test_fail_without_permission(self):
        self.gov_user.role = self.default_role
        self.gov_user.save()

        response = self.client.get(self.URL, **self.gov_headers)

        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)
