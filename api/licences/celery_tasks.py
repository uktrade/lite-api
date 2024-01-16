from celery import shared_task
from celery.utils.log import get_task_logger
from django.db import transaction

from api.licences.enums import LicenceStatus, HMRCIntegrationActionEnum
from api.licences.libraries.hmrc_integration_operations import HMRCIntegrationException, send_licence
from api.licences.models import Licence


MAX_ATTEMPTS = 5
RETRY_BACKOFF = 1200


logger = get_task_logger(__name__)


@shared_task(
    autoretry_for=(HMRCIntegrationException,),
    max_retries=MAX_ATTEMPTS,
    retry_backoff=RETRY_BACKOFF,
)
def send_licence_details_to_lite_hmrc(licence_id, action):
    """
    Sends licence details to lite-hmrc

    :param licence_id:
    :param action:
    """
    try:
        with transaction.atomic():
            # transaction.atomic + select_for_update + nowait=True will throw an error if row has already been locked
            logger.info("Attempt to acquire lock (non-blocking) before updating licence %s", str(licence_id))
            licence = Licence.objects.select_for_update(nowait=True).get(id=licence_id)
            send_licence(licence, action)
    except HMRCIntegrationException as e:
        logger.error("Error sending licence %s details to lite-hmrc: %s", str(licence_id), str(e))
        raise e


def schedule_licence_details_to_lite_hmrc(licence_id, action):
    licence = Licence.objects.get(id=licence_id)
    if (
        licence.status == LicenceStatus.ISSUED
        and action == HMRCIntegrationActionEnum.INSERT
        and licence.goods.count() == 0
    ):
        logger.info(
            "Licence %s contains no licenceable goods, skipping sending details to lite-hmrc",
            licence.reference_code,
        )
        return

    logger.info("Scheduling task to %s licence %s details to lite-hmrc", action, str(licence_id))
    send_licence_details_to_lite_hmrc.delay(licence_id, action)
