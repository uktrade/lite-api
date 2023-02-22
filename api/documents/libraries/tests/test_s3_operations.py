from unittest.mock import Mock, patch

from django.conf import settings
from django.test import override_settings, SimpleTestCase

from ..s3_operations import get_client


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
