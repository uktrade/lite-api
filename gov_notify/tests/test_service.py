from unittest import mock

from gov_notify import service
from gov_notify.enums import TemplateType
from gov_notify.tests.factories import GovNotifyTemplateFactory
from test_helpers.clients import DataTestClient


class GovNotifyTemplateTests(DataTestClient):
    def setUp(self):
        self.ecju_template = GovNotifyTemplateFactory(template_type=TemplateType.ECJU)

    @mock.patch("gov_notify.service.client")
    def test_send_email(self, mock_client):
        email = "fake@email.com"
        template_type = TemplateType.ECJU
        data = {"key": "value"}
        template_id = self.ecju_template.template_id

        service.send_email(email_address=email, template_type=template_type, data=data)

        mock_client.send_email.assert_called_with(email_address=email, template_id=template_id, data=data)
