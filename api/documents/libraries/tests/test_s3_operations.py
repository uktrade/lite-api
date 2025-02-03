import logging

from unittest.mock import (
    Mock,
    patch,
)

from moto import mock_aws

from botocore.exceptions import (
    BotoCoreError,
    ReadTimeoutError,
)

from django.http import FileResponse
from django.test import override_settings, SimpleTestCase

from test_helpers.s3 import S3TesterHelper

from ..s3_operations import (
    delete_file,
    document_download_stream,
    init_s3_client,
    get_object,
    upload_bytes_file,
)


@patch("api.documents.libraries.s3_operations.boto3")
@patch("api.documents.libraries.s3_operations.Config")
@override_settings(
    AWS_ENDPOINT_URL="AWS_ENDPOINT_URL",
    AWS_REGION="AWS_REGION",
    S3_CONNECT_TIMEOUT=22,
    S3_REQUEST_TIMEOUT=44,
)
class S3OperationsTests(SimpleTestCase):
    databases = {"default"}

    @override_settings(
        AWS_ENDPOINT_URL=None,
    )
    def test_get_client_without_aws_endpoint_url(self, mock_Config, mock_boto3):
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        returned_client = init_s3_client()
        self.assertEqual(returned_client, mock_client)

        mock_Config.assert_called_with(
            connect_timeout=22,
            read_timeout=44,
        )
        config = mock_Config(
            connection_timeout=22,
            read_timeout=44,
        )
        mock_boto3.client.assert_called_with(
            "s3",
            region_name="AWS_REGION",
            config=config,
        )

    def test_get_client_with_aws_endpoint_url(self, mock_Config, mock_boto3):
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        returned_client = init_s3_client()
        self.assertEqual(returned_client, mock_client)

        mock_Config.assert_called_with(
            connect_timeout=22,
            read_timeout=44,
        )
        config = mock_Config(
            connection_timeout=22,
            read_timeout=44,
        )
        mock_boto3.client.assert_called_with(
            "s3",
            region_name="AWS_REGION",
            config=config,
            endpoint_url="AWS_ENDPOINT_URL",
        )


@override_settings(
    AWS_STORAGE_BUCKET_NAME="test-bucket",
)
class S3OperationsGetObjectTests(SimpleTestCase):
    databases = {"default"}

    @patch("api.documents.libraries.s3_operations._client")
    def test_get_object(self, mock_client):
        mock_object = Mock()
        mock_client.get_object.return_value = mock_object

        returned_object = get_object("document-id", "s3-key")

        self.assertEqual(returned_object, mock_object)
        mock_client.get_object.assert_called_with(Bucket="test-bucket", Key="s3-key")

    @patch("api.documents.libraries.s3_operations._client")
    def test_get_object_read_timeout_error(self, mock_client):
        mock_client.get_object.side_effect = ReadTimeoutError(
            endpoint_url="endpoint_url",
        )

        with self.assertLogs(
            "api.documents.libraries.s3_operations",
            logging.WARNING,
        ) as al:
            returned_object = get_object("document-id", "s3-key")

        self.assertIsNone(returned_object)
        self.assertIn(
            "WARNING:api.documents.libraries.s3_operations:Timeout exceeded when retrieving file 's3-key' on document 'document-id'",
            al.output,
        )

    @patch("api.documents.libraries.s3_operations._client")
    def test_get_object_boto_core_error(self, mock_client):
        mock_client.get_object.side_effect = BotoCoreError()

        with self.assertLogs(
            "api.documents.libraries.s3_operations",
            logging.WARNING,
        ) as al:
            returned_object = get_object("document-id", "s3-key")

        self.assertIsNone(returned_object)
        self.assertIn(
            "WARNING:api.documents.libraries.s3_operations:An unexpected error occurred when retrieving file 's3-key' on document 'document-id': An unspecified error occurred",
            al.output,
        )


@mock_aws
class S3OperationsDeleteFileTests(SimpleTestCase):
    databases = {"default"}

    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)

        self.s3_test_helper = S3TesterHelper()

    def test_delete_file(self):
        self.s3_test_helper.add_test_file("s3-key", b"test")

        delete_file("document-id", "s3-key")

        self.s3_test_helper.assert_file_not_in_s3("s3-key")

    @patch("api.documents.libraries.s3_operations._client")
    def test_delete_file_read_timeout_error(self, mock_client):
        mock_client.delete_object.side_effect = ReadTimeoutError(
            endpoint_url="endpoint_url",
        )

        with self.assertLogs(
            "api.documents.libraries.s3_operations",
            logging.WARNING,
        ) as al:
            delete_file("document-id", "s3-key")

        self.assertIn(
            "WARNING:api.documents.libraries.s3_operations:Timeout exceeded when retrieving file 's3-key' on document 'document-id'",
            al.output,
        )

    @patch("api.documents.libraries.s3_operations._client")
    def test_delete_file_boto_core_error(self, mock_client):
        mock_client.delete_object.side_effect = BotoCoreError()

        with self.assertLogs(
            "api.documents.libraries.s3_operations",
            logging.WARNING,
        ) as al:
            delete_file("document-id", "s3-key")

        self.assertIn(
            "WARNING:api.documents.libraries.s3_operations:An unexpected error occurred when deleting file 's3-key' on document 'document-id': An unspecified error occurred",
            al.output,
        )


@mock_aws
class S3OperationsUploadBytesFileTests(SimpleTestCase):
    databases = {"default"}

    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)

        self.s3_test_helper = S3TesterHelper()

    def test_upload_bytes_file(self):
        upload_bytes_file(b"test", "s3-key")

        self.s3_test_helper.assert_file_in_s3("s3-key")
        self.s3_test_helper.assert_file_body("s3-key", b"test")


@mock_aws
class S3OperationsDocumentDownloadStreamTests(SimpleTestCase):
    databases = {"default"}

    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)

        self.s3_test_helper = S3TesterHelper()

    def test_document_download_stream(self):
        self.s3_test_helper.add_test_file("s3-key", b"test")

        mock_document = Mock()
        mock_document.id = "document-id"
        mock_document.s3_key = "s3-key"
        mock_document.name = "test.doc"

        response = document_download_stream(mock_document)

        self.assertIsInstance(response, FileResponse)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/msword")
        self.assertEqual(response["Content-Disposition"], 'attachment; filename="test.doc"')
        self.assertEqual(b"".join(response.streaming_content), b"test")
