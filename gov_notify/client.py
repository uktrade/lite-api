from django.conf import settings
from notifications_python_client import NotificationsAPIClient


class LiteNotificationClient:
    def send_email(self, email_address, template_id, data):
        client = NotificationsAPIClient(settings.GOV_NOTIFY_API_KEY)
        client.send_email_notification(email_address=email_address, template_id=template_id, personalisation=data)


client = LiteNotificationClient()
