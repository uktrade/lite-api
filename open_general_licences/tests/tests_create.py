from copy import deepcopy

from rest_framework import status
from rest_framework.reverse import reverse

from cases.enums import CaseTypeEnum
from open_general_licences.models import OpenGeneralLicence
from test_helpers.clients import DataTestClient

URL = reverse("open_general_licences:list")

REQUEST_DATA = {
    "name": "Open general export licence (low value shipments)",
    "description": "Licence allowing the export of low value shipments of certain goods.",
    "url": "https://www.gov.uk/government/publications/open-general-export-licence-low-value-shipments",
    "case_type": CaseTypeEnum.OGEL.id,
    "countries": ["CA"],
    "control_list_entries": ["ML1a"],
}


def _assert_response_data(self, response_data, request_data):
    self.assertEquals(response_data["name"], request_data["name"])
    self.assertEquals(response_data["description"], request_data["description"])
    self.assertEquals(response_data["url"], request_data["url"])
    self.assertEquals(response_data["case_type"], str(request_data["case_type"]))
    self.assertEquals(response_data["countries"], request_data["countries"])
    self.assertTrue(len(response_data["control_list_entries"]) > 0)
    for control_list_entry in response_data["control_list_entries"]:
        self.assertTrue(control_list_entry["rating"] in request_data["control_list_entries"])


class TestCreateOGL(DataTestClient):
    def setUp(self):
        super().setUp()
        self.request_data = deepcopy(REQUEST_DATA)

    def test_creating_with_default_request_data(self):
        response = self.client.post(URL, self.request_data, **self.gov_headers)

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        _assert_response_data(self, response.json(), self.request_data)
        self.assertEquals(OpenGeneralLicence.objects.all().count(), 1)
