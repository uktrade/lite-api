import logging
from typing import Optional

from django.conf import settings
from notifications_python_client.errors import HTTPError

from gov_notify.client import client
from gov_notify.payloads import EmailData


def send_email(email_address, template_type, data: Optional[EmailData] = None):
    """
    Send an email using the gov notify service.
    """
    if not settings.GOV_NOTIFY_ENABLED:
        logging.info({"gov_notify": "disabled"})
        return

    data = data.as_dict() if data else None
    try:
        return client.send_email(email_address=email_address, template_id=template_type.template_id, data=data)
    except HTTPError as e:
        logging.exception(e)
