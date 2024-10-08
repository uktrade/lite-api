from unittest.mock import patch

from freezegun import freeze_time

from moto import mock_aws

from django.test import TestCase
from django.utils import timezone

from api.documents.tests.factories import DocumentFactory
from test_helpers.s3 import S3TesterHelper


@mock_aws
class DocumentModelTests(TestCase):
    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)

        self.s3_test_helper = S3TesterHelper()

    def test_delete_s3_removes_object(self):
        self.s3_test_helper.add_test_file("s3-key", b"test")

        document = DocumentFactory(s3_key="s3-key")
        document.delete_s3()

        self.s3_test_helper.assert_file_not_in_s3("s3-key")

    def test_delete_s3_on_shared_file_retains_object(self):
        self.s3_test_helper.add_test_file("s3-key", b"test")

        document = DocumentFactory(s3_key="s3-key")
        another_document = DocumentFactory(s3_key="s3-key")

        document.delete_s3()
        self.s3_test_helper.assert_file_in_s3("s3-key")

        another_document.delete_s3()
        self.s3_test_helper.assert_file_in_s3("s3-key")

    def test_force_delete_s3_file_on_shared_file_retains_object(self):
        self.s3_test_helper.add_test_file("s3-key", b"test")

        document = DocumentFactory(s3_key="s3-key")
        DocumentFactory(s3_key="s3-key")

        document.delete_s3(force_delete=True)
        self.s3_test_helper.assert_file_not_in_s3("s3-key")

    @freeze_time("2020-01-01 12:00:01")
    @patch("api.documents.models.av_operations.scan_file_for_viruses")
    def test_scan_for_viruses_safe_file(self, mock_scan_file_for_viruses):
        self.s3_test_helper.add_test_file("s3-key", b"test")
        mock_scan_file_for_viruses.return_value = False

        document = DocumentFactory(s3_key="s3-key")
        is_safe = document.scan_for_viruses()

        self.assertIs(is_safe, True)
        mock_scan_file_for_viruses.assert_called()
        document.refresh_from_db()
        self.assertIs(document.safe, True)
        self.assertEqual(document.virus_scanned_at, timezone.now())
        self.s3_test_helper.assert_file_in_s3("s3-key")

    @freeze_time("2020-01-01 12:00:01")
    @patch("api.documents.models.av_operations.scan_file_for_viruses")
    def test_scan_for_viruses_unsafe_file(self, mock_scan_file_for_viruses):
        self.s3_test_helper.add_test_file("s3-key", b"test")
        mock_scan_file_for_viruses.return_value = True

        document = DocumentFactory(s3_key="s3-key")
        is_safe = document.scan_for_viruses()

        self.assertIs(is_safe, False)
        mock_scan_file_for_viruses.assert_called()
        document.refresh_from_db()
        self.assertIs(document.safe, False)
        self.assertEqual(document.virus_scanned_at, timezone.now())
        self.s3_test_helper.assert_file_not_in_s3("s3-key")

    @freeze_time("2020-01-01 12:00:01")
    @patch("api.documents.models.av_operations.scan_file_for_viruses")
    def test_scan_for_viruses_unsafe_shared_file(self, mock_scan_file_for_viruses):
        self.s3_test_helper.add_test_file("s3-key", b"test")
        mock_scan_file_for_viruses.return_value = True

        document = DocumentFactory(s3_key="s3-key")
        another_document = DocumentFactory(s3_key="s3-key")
        is_safe = document.scan_for_viruses()

        self.assertFalse(is_safe)
        mock_scan_file_for_viruses.assert_called()
        document.refresh_from_db()
        self.assertIs(document.safe, False)
        self.assertEqual(document.virus_scanned_at, timezone.now())
        self.s3_test_helper.assert_file_not_in_s3("s3-key")

        another_document.refresh_from_db()
        self.assertIs(another_document.safe, False)
        self.assertEqual(another_document.virus_scanned_at, timezone.now())
