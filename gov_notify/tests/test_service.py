from unittest import mock

from rest_framework.test import APITestCase

from gov_notify import service
from gov_notify.enums import TemplateType
from gov_notify.payloads import OrganisationStatusEmailData


class GovNotifyTemplateTests(APITestCase):
    @mock.patch("gov_notify.service.client")
    def test_send_email(self, mock_client):
        email = "fake@email.com"
        template_type = TemplateType.ORGANISATION_STATUS
        data = {"organisation_name": "testorgname"}

        organisation_status_data = OrganisationStatusEmailData(**data)

        service.send_email(email_address=email, template_type=template_type, data=organisation_status_data)

        mock_client.send_email.assert_called_with(
            email_address=email, template_id=TemplateType.ORGANISATION_STATUS.template_id, data=data
        )
