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
            # It is essential to use select_for_update() without nowait=True because
            # if lock is not available then we need to wait here till it is available.
            #
            # This task is scheduled when licence is issued which is already part of a transaction.
            # Licence row would've already been locked during that transaction so if continue
            # without waiting it will result in OperationalError.
            # Wait here till it is released at which point this continues execution.
            logger.info("Attempt to acquire lock (blocking) before updating licence %s", str(licence_id))
            licence = Licence.objects.select_for_update().get(id=licence_id)

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

    logger.info("Scheduling task to %s licence %s details in lite-hmrc", action, licence.reference_code)

    send_licence_details_to_lite_hmrc.delay(licence_id, action)
