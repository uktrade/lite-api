from unittest import mock

from django.test import override_settings
from rest_framework.test import APITestCase

from gov_notify import service
from gov_notify.enums import TemplateType
from gov_notify.payloads import ExporterRegistration


class GovNotifyTemplateTests(APITestCase):
    @override_settings(CELERY_ALWAYS_EAGER=True)
    @mock.patch("api.core.celery_tasks.send_email.apply_async")
    def test_send_email(self, mock_send_email):
        email = "fake@email.com"
        template_type = TemplateType.EXPORTER_REGISTERED_NEW_ORG
        data = {"organisation_name": "testorgname"}

        organisation_status_data = ExporterRegistration(**data)

        service.send_email(email_address=email, template_type=template_type, data=organisation_status_data)

        assert mock_send_email.called

    @override_settings(GOV_NOTIFY_ENABLED=False)
    @mock.patch("api.core.celery_tasks.send_email.apply_async")
    def test_send_email_with_gov_notify_disabled(self, mock_send_email):
        email = "fake@email.com"
        template_type = TemplateType.EXPORTER_REGISTERED_NEW_ORG
        data = {"organisation_name": "testorgname"}

        organisation_status_data = ExporterRegistration(**data)

        service.send_email(email_address=email, template_type=template_type, data=organisation_status_data)

        assert mock_send_email.called is False
