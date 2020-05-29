from gov_notify.models import GovNotifyTemplate
from gov_notify.client import client


def send_email(email_address, template_type, data=None):
    template_id = GovNotifyTemplate.objects.get(template_type=template_type).template_id

    response = client.send_email(email_address=email_address, template_id=template_id, data=data)

    return response
