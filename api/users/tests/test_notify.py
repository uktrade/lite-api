from unittest import mock

from faker import Faker
from rest_framework.test import APITestCase

from gov_notify.enums import TemplateType
from gov_notify.payloads import ExporterUserAdded
from api.users.notify import notify_exporter_user_added


class NotifyTests(APITestCase):
    @mock.patch("api.users.notify.send_email")
    def test_notify_exporter_user_added(self, mock_send_email):
        email = Faker().email()
        data = {"organisation_name": "testorgname", "exporter_frontend_url": "https://some.domain/foo/"}
        expected_payload = ExporterUserAdded(**data)

        notify_exporter_user_added(email, data)

        mock_send_email.assert_called_with(email, TemplateType.EXPORTER_USER_ADDED, expected_payload)
