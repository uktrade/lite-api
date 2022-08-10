import logging
from typing import Optional

from django.conf import settings

from gov_notify.payloads import EmailData
from api.core.celery_tasks import send_email as celery_send_email


logger = logging.getLogger(__name__)


def send_email(email_address, template_type, data: Optional[EmailData] = None):
    """
    Send an email using the gov notify service via celery.
    """
    if not settings.GOV_NOTIFY_ENABLED:
        logging.info({"gov_notify": "disabled"})
        return

    data = data.as_dict() if data else None
    logger.info("sending email via celery")
    return celery_send_email.apply_async([email_address, template_type.template_id, data])
