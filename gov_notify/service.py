from typing import Optional

from gov_notify.client import client
from gov_notify.payloads import EmailData


def send_email(email_address, template_type, data: Optional[EmailData] = None):
    data = data.as_dict() if data else None
    response = client.send_email(email_address=email_address, template_id=template_type.template_id, data=data)

    return response
