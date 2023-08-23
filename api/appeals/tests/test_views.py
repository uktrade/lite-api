from unittest import mock

from django.urls import reverse
from django.utils.timezone import now

from rest_framework import status

from test_helpers.clients import DataTestClient

from ..factories import Appeal


class TestAppealDocuments(DataTestClient):
    def setUp(self):
        super().setUp()

        self.appeal = Appeal()
        self.appeal.save()
        self.url = reverse("appeals:documents", kwargs={"pk": self.appeal.pk})

    @mock.patch("api.documents.models.Document.scan_for_viruses", autospec=True)
    def test_creating_document(self, mock_scan_for_viruses):
        def set_safe(document):
            document.safe = True
            document.virus_scanned_at = now()
            document.save()

        mock_scan_for_viruses.side_effect = set_safe

        response = self.client.post(
            self.url,
            {
                "name": "file 1",
                "s3_key": "file 1",
                "size": "256",
            },
            **self.exporter_headers,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        mock_scan_for_viruses.assert_called()

        document = self.appeal.documents.first()
        self.assertEqual(document.name, "file 1")
        self.assertEqual(document.s3_key, "file 1")
        self.assertEqual(document.size, 256)
        self.assertTrue(document.safe)

        self.assertEqual(
            response.json(),
            {
                "id": str(document.pk),
                "name": "file 1",
                "size": 256,
                "s3_key": "file 1",
                "safe": True,
            },
        )

    def test_creating_document_with_invalid_appeal_pk(self):
        url = reverse("appeals:documents", kwargs={"pk": "543f3c7c-3815-4cd6-af4d-2a852564faac"})
        response = self.client.post(
            url,
            {
                "name": "file 1",
                "s3_key": "file 1",
                "size": "256",
            },
            **self.exporter_headers,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
