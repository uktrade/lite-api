import logging

from django.utils import timezone
from rest_framework import status

from conf.requests import post
from conf.settings import LITE_HMRC_INTEGRATION_URL, LITE_HMRC_REQUEST_TIMEOUT, HAWK_LITE_API_CREDENTIALS
from licences.models import Licence
from licences.serializers.hmrc_integration import HMRCIntegrationLicenceSerializer

SEND_LICENCE_ENDPOINT = "/mail/update-licence/"


class HMRCIntegrationException(Exception):
    """Exceptions to raise when sending requests to the HMRC Integration service."""


def send_licence(licence: Licence):
    logging.info(f"Sending licence '{licence.id}' changes to HMRC Integration")

    url = f"{LITE_HMRC_INTEGRATION_URL}{SEND_LICENCE_ENDPOINT}"
    data = {"licence": HMRCIntegrationLicenceSerializer(licence).data}

    response = post(url, data, hawk_credentials=HAWK_LITE_API_CREDENTIALS, timeout=LITE_HMRC_REQUEST_TIMEOUT)

    if response.status_code not in [status.HTTP_201_CREATED, status.HTTP_304_NOT_MODIFIED]:
        raise HMRCIntegrationException(
            f"An unexpected response was received when sending licence '{licence.id}' changes to HMRC Integration -> "
            f"status={response.status_code}, message={response.text}"
        )

    licence.set_sent_at(timezone.now())

    logging.info(f"Successfully sent licence '{licence.id}' changes to HMRC Integration")
