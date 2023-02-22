from contextlib import contextmanager
from unittest.mock import Mock, patch

from moto import mock_aws

from django.conf import settings
from django.http import StreamingHttpResponse
from django.test import override_settings, SimpleTestCase

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
    AWS_ACCESS_KEY_ID="AWS_ACCESS_KEY_ID",
    AWS_SECRET_ACCESS_KEY="AWS_SECRET_ACCESS_KEY",
    AWS_REGION="AWS_REGION",
    S3_CONNECT_TIMEOUT=22,
    S3_REQUEST_TIMEOUT=44,
)
class S3OperationsTests(SimpleTestCase):
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
            aws_access_key_id="AWS_ACCESS_KEY_ID",
            aws_secret_access_key="AWS_SECRET_ACCESS_KEY",
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
            aws_access_key_id="AWS_ACCESS_KEY_ID",
            aws_secret_access_key="AWS_SECRET_ACCESS_KEY",
            region_name="AWS_REGION",
            config=config,
            endpoint_url="AWS_ENDPOINT_URL",
        )


@override_settings(
    AWS_STORAGE_BUCKET_NAME="test-bucket",
)
class S3OperationsGetObjectTests(SimpleTestCase):
    @patch("api.documents.libraries.s3_operations._client")
    def test_get_object(self, mock_client):
        mock_object = Mock()
        mock_client.get_object.return_value = mock_object

        returned_object = get_object("document-id", "s3-key")

        self.assertEqual(returned_object, mock_object)
        mock_client.get_object.assert_called_with(Bucket="test-bucket", Key="s3-key")


@contextmanager
def _create_bucket(s3):
    s3.create_bucket(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        CreateBucketConfiguration={
            "LocationConstraint": settings.AWS_REGION,
        },
    )
    yield


@mock_aws
class S3OperationsDeleteFileTests(SimpleTestCase):
    def test_delete_file(self):
        s3 = init_s3_client()
        with _create_bucket(s3):
            s3.put_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key="s3-key",
                Body=b"test",
            )

            delete_file("document-id", "s3-key")

            objs = s3.list_objects(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
            keys = [o["Key"] for o in objs.get("Contents", [])]
            self.assertNotIn("s3-key", keys)


@mock_aws
class S3OperationsUploadBytesFileTests(SimpleTestCase):
    def test_upload_bytes_file(self):
        s3 = init_s3_client()
        with _create_bucket(s3):
            upload_bytes_file(b"test", "s3-key")

            obj = s3.get_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key="s3-key",
            )
            self.assertEqual(obj["Body"].read(), b"test")


@mock_aws
class S3OperationsDocumentDownloadStreamTests(SimpleTestCase):
    def test_document_download_stream(self):
        s3 = init_s3_client()
        with _create_bucket(s3):
            s3.put_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key="s3-key",
                Body=b"test",
            )

            mock_document = Mock()
            mock_document.id = "document-id"
            mock_document.s3_key = "s3-key"
            mock_document.name = "test.doc"

            response = document_download_stream(mock_document)

        self.assertIsInstance(response, StreamingHttpResponse)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/msword")
        self.assertEqual(response["Content-Disposition"], 'attachment; filename="test.doc"')
        self.assertEqual(b"".join(response.streaming_content), b"test")
