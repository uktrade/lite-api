from unittest import mock

from rest_framework.test import APITestCase
from django.test import override_settings

from gov_notify.client import LiteNotificationClient


class LiteNotificationClientTests(APITestCase):

    @override_settings(GOV_NOTIFY_ENABLED=False)
    @mock.patch("gov_notify.client.NotificationsAPIClient")
    def test_send_email_notify_disabled(self, mock_client):
        api_key = "testapikey"
        client = LiteNotificationClient(api_key)
        client.send_email(
            "test@example.com",
            "test-template-id",
            {},
        )
        # Ensure that the govuk notifcation client was not called when the notify
        # setting is disabled
        assert not mock_client.called

    @override_settings(GOV_NOTIFY_ENABLED=True)
    @mock.patch("gov_notify.client.NotificationsAPIClient")
    def test_send_email_notify_enabled(self, mock_client):
        api_key = "testapikey"
        client = LiteNotificationClient(api_key)
        email = "test@example.com"
        template_id = "test-template-id"
        personalisation = {}
        client.send_email(
            email,
            template_id,
            personalisation,
        )
        # Ensure that govuk notification client was instantiated and called as expected
        mock_client.assert_called_with(api_key)
        mock_client.return_value.send_email_notification.assert_called_with(
            email_address=email,
            template_id=template_id,
            personalisation=personalisation,
        )

