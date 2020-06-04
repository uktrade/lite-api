import logging

from django.conf import settings
from notifications_python_client import NotificationsAPIClient


class LiteNotificationClient:
    """
    Adapter class for communicating with Gov Notify API.
    """

    def __init__(self, api_key):
        self.api_key = api_key

    def send_email(self, email_address, template_id, data):
        if not settings.GOV_NOTIFY_ENABLED:
            logging.info({"gov_notify": "disabled"})
            return

        return NotificationsAPIClient(self.api_key).send_email_notification(
            email_address=email_address, template_id=template_id, personalisation=data
        )


client = LiteNotificationClient(api_key=settings.GOV_NOTIFY_KEY)
