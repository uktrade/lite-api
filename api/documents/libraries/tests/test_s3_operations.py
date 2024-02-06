from contextlib import contextmanager
from unittest.mock import Mock, patch

from moto import mock_aws

from django.conf import settings
from django.http import FileResponse
from django.test import override_settings, SimpleTestCase

from ..s3_operations import (
    delete_file,
    document_download_stream,
    init_s3_client,
    get_object,
    move_staged_document_to_processed,
    upload_bytes_file,
)


TEST_AWS_BUCKET_NAME = settings.FILE_UPLOAD_PROCESSED_BUCKET["AWS_STORAGE_BUCKET_NAME"]


@patch("api.documents.libraries.s3_operations.boto3")
@patch("api.documents.libraries.s3_operations.Config")
@override_settings(
    AWS_ENDPOINT_URL="AWS_ENDPOINT_URL",
    FILE_UPLOAD_PROCESSED_BUCKET={
        "AWS_ACCESS_KEY_ID": "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY": "AWS_SECRET_ACCESS_KEY",
        "AWS_REGION": "AWS_REGION",
    },
    FILE_UPLOAD_STAGED_BUCKET={
        "AWS_ACCESS_KEY_ID": "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY": "AWS_SECRET_ACCESS_KEY",
        "AWS_REGION": "AWS_REGION",
    },
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
        self.assertEqual(returned_client["processed"], mock_client)
        self.assertEqual(returned_client["staged"], mock_client)

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
        self.assertEqual(returned_client["processed"], mock_client)
        self.assertEqual(returned_client["staged"], mock_client)

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
    FILE_UPLOAD_PROCESSED_BUCKET={
        "AWS_ACCESS_KEY_ID": "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY": "AWS_SECRET_ACCESS_KEY",
        "AWS_REGION": "AWS_REGION",
        "AWS_STORAGE_BUCKET_NAME": "test-bucket",
    },
)
class S3OperationsGetObjectTests(SimpleTestCase):
    @patch("api.documents.libraries.s3_operations._processed_client")
    def test_get_object(self, mock_client):
        mock_object = Mock()
        mock_client.get_object.return_value = mock_object

        returned_object = get_object("document-id", "s3-key")

        self.assertEqual(returned_object, mock_object)
        mock_client.get_object.assert_called_with(Bucket="test-bucket", Key="s3-key")


class S3OperationsMoveStagedDocumentToProcessedTests(SimpleTestCase):
    @patch("api.documents.libraries.s3_operations._staged_client")
    @patch("api.documents.libraries.s3_operations._processed_client")
    def test_get_object(self, mock_processed_client, mock_staged_client):
        mock_staged_body = Mock()
        mock_staged_file = {"Body": mock_staged_body}
        mock_staged_client.get_object.return_value = mock_staged_file

        move_staged_document_to_processed("document-id", "s3-key")

        mock_staged_client.get_object.assert_called_with(Bucket="staged", Key="s3-key")
        mock_processed_client.put_object.assert_called_with(
            Bucket="processed", Key="s3-key", Body=mock_staged_body.read()
        )
        mock_staged_client.delete_object.assert_called_with(Bucket="staged", Key="s3-key")


@contextmanager
def _create_bucket(s3):
    s3.create_bucket(
        Bucket=TEST_AWS_BUCKET_NAME,
        CreateBucketConfiguration={
            "LocationConstraint": settings.FILE_UPLOAD_PROCESSED_BUCKET["AWS_REGION"],
        },
    )
    yield


def get_s3_client():
    return init_s3_client()["processed"]


@mock_aws
class S3OperationsDeleteFileTests(SimpleTestCase):
    def test_delete_file(self):
        s3 = get_s3_client()
        with _create_bucket(s3):
            s3.put_object(
                Bucket=TEST_AWS_BUCKET_NAME,
                Key="s3-key",
                Body=b"test",
            )

            delete_file("document-id", "s3-key")

            objs = s3.list_objects(Bucket=TEST_AWS_BUCKET_NAME)
            keys = [o["Key"] for o in objs.get("Contents", [])]
            self.assertNotIn("s3-key", keys)


@mock_aws
class S3OperationsUploadBytesFileTests(SimpleTestCase):
    def test_upload_bytes_file(self):
        s3 = get_s3_client()
        with _create_bucket(s3):
            upload_bytes_file(b"test", "s3-key")

            obj = s3.get_object(
                Bucket=TEST_AWS_BUCKET_NAME,
                Key="s3-key",
            )
            self.assertEqual(obj["Body"].read(), b"test")


@mock_aws
class S3OperationsDocumentDownloadStreamTests(SimpleTestCase):
    def test_document_download_stream(self):
        s3 = get_s3_client()
        with _create_bucket(s3):
            s3.put_object(
                Bucket=TEST_AWS_BUCKET_NAME,
                Key="s3-key",
                Body=b"test",
            )

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
