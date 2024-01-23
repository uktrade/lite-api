import pytest

from unittest import mock
from api.documents.libraries.process_document import process_document
from test_helpers.clients import DataTestClient
from django.utils.timezone import now

from rest_framework.exceptions import ValidationError
from api.documents.celery_tasks import scan_document_for_viruses, delete_document_from_s3


class DocumentVirusScan(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_standard_application_case(self.organisation)

    @mock.patch("api.documents.libraries.s3_operations.get_object")
    @mock.patch("api.documents.libraries.av_operations.scan_file_for_viruses")
    def test_document_scan_document_success(self, mock_virus_scan, mock_s3_operations_get_object):
        mock_s3_operations_get_object.return_value = {
            "name": "updated_document_name.pdf",
            "s3_key": "s3_keykey.pdf",
            "size": 123456,
        }
        mock_virus_scan.return_value = False
        document = self.create_case_document(case=self.case, user=self.gov_user, name="jimmy")
        self.assertIsNone(document.virus_scanned_at)

        scan_document_for_viruses(str(document.id))
        document.refresh_from_db()
        self.assertIsNotNone(document.virus_scanned_at)
        self.assertTrue(document.safe)

        mock_virus_scan.called_once()
        mock_s3_operations_get_object.called_once()

    @mock.patch("api.documents.models.Document.scan_for_viruses")
    def test_document_scan_document_for_viruses_called(self, mock_document_scan_for_viruses):

        document = self.create_case_document(case=self.case, user=self.gov_user, name="jimmy")
        scan_document_for_viruses(str(document.id))
        mock_document_scan_for_viruses.called_once()

    @mock.patch("api.documents.celery_tasks.scan_document_for_viruses.apply_async")
    def test_process_document_raises_validation_exception(self, mock_scan_for_viruses):
        # given there is a case document

        document = self.create_case_document(case=self.case, user=self.gov_user, name="jimmy")

        mock_scan_for_viruses.side_effect = Exception("Failed to get document")
        with pytest.raises(ValidationError):
            process_document(document)

    def test_scan_document_for_viruses_already_virus_scanned(self):

        document = self.create_case_document(case=self.case, user=self.gov_user, name="jimmy")
        document.virus_scanned_at = now()
        document.save()
        response = scan_document_for_viruses(str(document.id))
        self.assertEqual(response, None)

    @mock.patch("api.documents.models.Document.scan_for_viruses")
    def test_document_scan_document_raises_exception(self, mock_document_scan_for_viruses):

        document = self.create_case_document(case=self.case, user=self.gov_user, name="jimmy")
        scan_document_for_viruses(str(document.id))
        mock_document_scan_for_viruses.side_effect = Exception("Failed")

        with pytest.raises(Exception):
            scan_document_for_viruses(str(document.id))

    @mock.patch("api.documents.models.Document.delete_s3")
    def test_delete_document_calls_s3_delete(self, mock_delete_s3):
        document = self.create_case_document(case=self.case, user=self.gov_user, name="jimmy")
        delete_document_from_s3(str(document.id))
        mock_delete_s3.called_once()
