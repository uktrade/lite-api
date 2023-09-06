from unittest import mock

from django.urls import reverse
from django.utils.timezone import now

from rest_framework import status

from test_helpers.clients import DataTestClient

from .factories import (
    AppealFactory,
    AppealDocumentFactory,
)


class TestAppealDocuments(DataTestClient):
    def setUp(self):
        super().setUp()

        self.appeal = AppealFactory()
        application = self.create_standard_application_case(
            organisation=self.exporter_user.organisation,
        )
        application.appeal = self.appeal
        application.save()
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

    def test_creating_document_with_different_organisation(self):
        self.appeal.baseapplication.organisation = self.create_organisation_with_exporter_user()[0]
        self.appeal.baseapplication.save()

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
            status.HTTP_403_FORBIDDEN,
        )

    def test_get_document(self):
        appeal_document = AppealDocumentFactory(appeal=self.appeal)

        url = reverse(
            "appeals:document",
            kwargs={
                "pk": str(self.appeal.pk),
                "document_pk": str(appeal_document.pk),
            },
        )
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.json(),
            {
                "id": str(appeal_document.pk),
                "name": appeal_document.name,
                "s3_key": appeal_document.s3_key,
                "safe": appeal_document.safe,
                "size": appeal_document.size,
            },
        )

    def test_get_document_invalid_appeal_pk(self):
        appeal_document = AppealDocumentFactory(appeal=self.appeal)

        url = reverse(
            "appeals:document",
            kwargs={
                "pk": "0f415f8a-e3e8-4c49-b053-ef03b1c477d5",
                "document_pk": str(appeal_document.pk),
            },
        )
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_get_document_invalid_document_pk(self):
        url = reverse(
            "appeals:document",
            kwargs={
                "pk": str(self.appeal.pk),
                "document_pk": "0b551122-1ac2-4ea2-82b3-f1aaf0bf4923",
            },
        )
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_get_document_different_organisation(self):
        self.appeal.baseapplication.organisation = self.create_organisation_with_exporter_user()[0]
        self.appeal.baseapplication.save()
        appeal_document = AppealDocumentFactory(appeal=self.appeal)

        url = reverse(
            "appeals:document",
            kwargs={
                "pk": str(self.appeal.pk),
                "document_pk": str(appeal_document.pk),
            },
        )
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
