from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient


class CertificateDownload(DataTestClient):
    def test_certificate_download(self):
        url = reverse("documents:certificate")
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.content)
