from copy import deepcopy

from parameterized import parameterized
from rest_framework import status
from rest_framework.reverse import reverse

from api.audit_trail.models import Audit
from api.cases.enums import CaseTypeEnum
from api.open_general_licences.models import OpenGeneralLicence
from test_helpers.clients import DataTestClient

URL = reverse("open_general_licences:list")

REQUEST_DATA = {
    "name": "Open general export licence (low value shipments)",
    "description": "Licence allowing the export of low value shipments of certain goods.",
    "url": "https://www.gov.uk/government/publications/open-general-export-licence-low-value-shipments",
    "case_type": CaseTypeEnum.OGEL.id,
    "countries": ["CA"],
    "control_list_entries": ["ML1a"],
    "registration_required": True,
}


def _assert_response_data(self, response_data, request_data):
    self.assertEqual(response_data["name"], request_data["name"])
    self.assertEqual(response_data["description"], request_data["description"])
    self.assertEqual(response_data["url"], request_data["url"])
    self.assertEqual(response_data["case_type"]["id"], str(request_data["case_type"]))

    self.assertTrue(len(response_data["countries"]) > 0)
    for country in response_data["countries"]:
        self.assertTrue(country["id"] in request_data["countries"])

    self.assertTrue(len(response_data["control_list_entries"]) > 0)
    for control_list_entry in response_data["control_list_entries"]:
        self.assertTrue(control_list_entry["rating"] in request_data["control_list_entries"])


class TestCreateOGL(DataTestClient):
    def setUp(self):
        super().setUp()
        self.request_data = deepcopy(REQUEST_DATA)
        self.gov_user.role = self.super_user_role
        self.gov_user.save()

    def test_creating_success(self):
        response = self.client.post(URL, self.request_data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        _assert_response_data(self, response.json(), self.request_data)
        self.assertEqual(OpenGeneralLicence.objects.all().count(), 1)
        self.assertEqual(Audit.objects.all().count(), 1)

    @parameterized.expand([(CaseTypeEnum.OGEL.id,), (CaseTypeEnum.OGTL.id,), (CaseTypeEnum.OGTCL.id,)])
    def test_creating_with_with_each_type_of_case_type(self, case_type_id):
        self.request_data["case_type"] = case_type_id
        response = self.client.post(URL, self.request_data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        _assert_response_data(self, response.json(), self.request_data)
        self.assertEqual(OpenGeneralLicence.objects.all().count(), 1)
        self.assertEqual(Audit.objects.all().count(), 1)

    @parameterized.expand(REQUEST_DATA.keys())
    # Since all fields are required in creation,
    # we get the list of fields though the key, and test it fails with each one
    def test_fail_creating_without_field(self, key):
        self.request_data.pop(key)
        response = self.client.post(URL, self.request_data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Audit.objects.all().count(), 0)

    @parameterized.expand(REQUEST_DATA.keys())
    # Since all fields are required in creation,
    # we get the list of fields though the key, and test it fails with each one
    def test_fail_creating_with_none_fields(self, key):
        self.request_data[key] = None
        response = self.client.post(URL, self.request_data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Audit.objects.all().count(), 0)

    @parameterized.expand(REQUEST_DATA.keys())
    # Since all fields are required in creation,
    # we get the list of fields though the key, and test it fails with each one
    def test_fail_creating_with_blank_fields(self, key):
        if isinstance(self.request_data[key], list):
            self.request_data[key] = []
        else:
            self.request_data[key] = ""
        self.request_data.pop(key)
        response = self.client.post(URL, self.request_data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Audit.objects.all().count(), 0)

    def test_fail_without_permission(self):
        self.gov_user.role = self.default_role
        self.gov_user.save()

        response = self.client.post(URL, self.request_data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
