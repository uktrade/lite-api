from unittest.mock import Mock, patch

from django.test import override_settings, SimpleTestCase

from ..s3_operations import (
    delete_file,
    get_client,
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
class S3OperationsGetClientTests(SimpleTestCase):
    @override_settings(
        AWS_ENDPOINT_URL=None,
    )
    def test_get_client_without_aws_endpoint_url(self, mock_Config, mock_boto3):
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        returned_client = get_client()
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

        returned_client = get_client()
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


@override_settings(
    AWS_STORAGE_BUCKET_NAME="test-bucket",
)
class S3OperationsDeleteFileTests(SimpleTestCase):
    @patch("api.documents.libraries.s3_operations._client")
    def test_delete_file(self, mock_client):
        delete_file("document-id", "s3-key")

        mock_client.delete_object.assert_called_with(Bucket="test-bucket", Key="s3-key")


@override_settings(
    AWS_STORAGE_BUCKET_NAME="test-bucket",
)
class S3OperationsUploadBytesFileTests(SimpleTestCase):
    @patch("api.documents.libraries.s3_operations._client")
    def test_upload_bytes_file(self, mock_client):
        mock_file = Mock()

        upload_bytes_file(mock_file, "s3-key")

        mock_client.put_object.assert_called_with(Bucket="test-bucket", Key="s3-key", Body=mock_file)
