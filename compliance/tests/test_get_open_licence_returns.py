from rest_framework import status
from rest_framework.reverse import reverse

from compliance.tests.factories import OpenLicenceReturnsFactory
from test_helpers.clients import DataTestClient


class GetOpenLicenceReturnsTest(DataTestClient):
    def setUp(self):
        super().setUp()
        application = self.create_standard_application_case(self.organisation)
        self.licence = self.create_licence(application, is_complete=True)
        self.olr = OpenLicenceReturnsFactory(organisation=self.organisation)
        self.olr.licences.set([self.licence])

    def test_get_open_licence_returns(self):
        url = reverse("compliance:open_licence_returns")
        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()["results"][0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["id"], str(self.olr.id))
        self.assertEqual(response_data["year"], self.olr.year)
        self.assertIsNotNone(response_data["created_at"])

    def test_get_open_licence_return(self):
        url = reverse("compliance:open_licence_return_download", kwargs={"pk": self.olr.id})
        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["id"], str(self.olr.id))
        self.assertEqual(response_data["year"], self.olr.year)
        self.assertIsNotNone(response_data["created_at"])
        self.assertEqual(response_data["returns_data"], self.olr.returns_data)
