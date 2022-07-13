from unittest import mock

from faker import Faker
from rest_framework.test import APITestCase

from gov_notify.enums import TemplateType
from gov_notify.payloads import ExporterRegistration
from api.organisations.notify import notify_exporter_registration


class NotifyTests(APITestCase):
    @mock.patch("api.organisations.notify.send_email")
    def test_notify_exporter_registration(self, mock_send_email):
        email = Faker().email()
        data = {"organisation_name": "testorgname"}
        expected_payload = ExporterRegistration(**data)

        notify_exporter_registration(email, data)

        mock_send_email.assert_called_with(email, TemplateType.EXPORTER_REGISTERED_NEW_ORG, expected_payload)
