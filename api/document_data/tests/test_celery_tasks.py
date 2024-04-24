import datetime

from unittest import mock

from moto import mock_aws

from botocore.exceptions import ClientError

from django.test import override_settings
from django.utils import timezone

from test_helpers.clients import DataTestClient

from api.documents.tests.factories import DocumentFactory
from api.document_data.celery_tasks import backup_document_data
from api.document_data.models import DocumentData


@mock_aws
class TestBackupDocumentData(DataTestClient):
    def setUp(self):
        super().setUp()
        self.create_default_bucket()

    def test_backup_new_document_data(self):
        self.put_object_in_default_bucket("thisisakey", b"test")
        DocumentFactory.create(
            s3_key="thisisakey",
            safe=True,
        )
        self.assertEqual(
            DocumentData.objects.count(),
            0,
        )

        backup_document_data.apply()

        self.assertEqual(
            DocumentData.objects.count(),
            1,
        )
        document_data = DocumentData.objects.get()
        self.assertEqual(
            document_data.s3_key,
            "thisisakey",
        )
        self.assertEqual(
            document_data.data,
            b"test",
        )
        s3_object = self.get_object_from_default_bucket("thisisakey")
        self.assertEqual(
            document_data.last_modified,
            s3_object["LastModified"],
        )
        self.assertEqual(
            document_data.content_type,
            s3_object["ContentType"],
        )

    def test_update_existing_document_data(self):
        self.put_object_in_default_bucket("thisisakey", b"test")
        DocumentFactory.create(
            s3_key="thisisakey",
            safe=True,
        )
        self.assertEqual(
            DocumentData.objects.count(),
            0,
        )

        backup_document_data.apply()
        self.assertEqual(
            DocumentData.objects.count(),
            1,
        )

        document_data = DocumentData.objects.get()
        document_data.last_modified = timezone.now() - datetime.timedelta(days=5)
        document_data.save()
        self.put_object_in_default_bucket("thisisakey", b"new contents")

        backup_document_data.apply()

        self.assertEqual(
            DocumentData.objects.count(),
            1,
        )
        document_data = DocumentData.objects.get()
        self.assertEqual(
            document_data.s3_key,
            "thisisakey",
        )
        self.assertEqual(
            document_data.data,
            b"new contents",
        )
        s3_object = self.get_object_from_default_bucket("thisisakey")
        self.assertEqual(
            document_data.last_modified,
            s3_object["LastModified"],
        )
        self.assertEqual(
            document_data.content_type,
            s3_object["ContentType"],
        )

    def test_leave_existing_document_data(self):
        self.put_object_in_default_bucket("thisisakey", b"test")
        DocumentFactory.create(
            s3_key="thisisakey",
            safe=True,
        )
        self.assertEqual(
            DocumentData.objects.count(),
            0,
        )

        backup_document_data.apply()
        self.assertEqual(
            DocumentData.objects.count(),
            1,
        )

        document_data = DocumentData.objects.get()
        document_data.last_modified = original_last_modified = timezone.now() + datetime.timedelta(days=5)
        document_data.save()
        self.put_object_in_default_bucket("thisisakey", b"new contents")

        backup_document_data.apply()

        self.assertEqual(
            DocumentData.objects.count(),
            1,
        )
        document_data = DocumentData.objects.get()
        self.assertEqual(
            document_data.s3_key,
            "thisisakey",
        )
        self.assertEqual(
            document_data.data,
            b"test",
        )
        self.assertEqual(
            document_data.last_modified,
            original_last_modified,
        )

    @mock.patch("api.document_data.celery_tasks.get_object")
    def test_ignore_client_error(self, mock_get_object):
        mock_get_object.side_effect = ClientError({}, "fake operation")

        self.put_object_in_default_bucket("thisisakey", b"test")
        DocumentFactory.create(
            s3_key="thisisakey",
            safe=True,
        )
        self.assertEqual(
            DocumentData.objects.count(),
            0,
        )

        backup_document_data.apply()
        self.assertEqual(
            DocumentData.objects.count(),
            0,
        )

    @mock.patch("api.document_data.celery_tasks.get_object")
    def test_ignore_get_object_returning_none(self, mock_get_object):
        mock_get_object.return_value = None

        self.put_object_in_default_bucket("thisisakey", b"test")
        DocumentFactory.create(
            s3_key="thisisakey",
            safe=True,
        )
        self.assertEqual(
            DocumentData.objects.count(),
            0,
        )

        backup_document_data.apply()
        self.assertEqual(
            DocumentData.objects.count(),
            0,
        )

    @override_settings(
        BACKUP_DOCUMENT_DATA_TO_DB=False,
    )
    def test_stop_backup_new_document_data(self):
        self.put_object_in_default_bucket("thisisakey", b"test")
        DocumentFactory.create(
            s3_key="thisisakey",
            safe=True,
        )
        self.assertEqual(
            DocumentData.objects.count(),
            0,
        )

        backup_document_data.apply()

        self.assertEqual(
            DocumentData.objects.count(),
            0,
        )
