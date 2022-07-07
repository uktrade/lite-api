from unittest import mock

from rest_framework.test import APITestCase

from gov_notify import service
from gov_notify.enums import TemplateType
from gov_notify.payloads import EcjuCreatedEmailData


class GovNotifyTemplateTests(APITestCase):
    @mock.patch("gov_notify.service.client")
    def test_send_email(self, mock_client):
        email = "fake@email.com"
        template_type = TemplateType.ECJU_CREATED
        data = {"case_reference": "123", "application_reference": "456", "link": "http"}

        ecju_email_data = EcjuCreatedEmailData(
            case_reference=data["case_reference"],
            application_reference=data["application_reference"],
            link=data["link"],
        )

        service.send_email(email_address=email, template_type=template_type, data=ecju_email_data)

        mock_client.send_email.assert_called_with(
            email_address=email, template_id=TemplateType.ECJU_CREATED.template_id, data=data
        )
