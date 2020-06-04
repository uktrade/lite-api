from rest_framework import status

from conf.requests import post
from conf.settings import LITE_HMRC_INTEGRATION_URL, LITE_HMRC_REQUEST_TIMEOUT
from licences.models import Licence
from licences.serializers.hmrc_integration import HMRCIntegrationLicenceSerializer

HAWK_CREDENTIALS = "lite-api"
SEND_LICENCE_ENDPOINT = "/mail/update-licence/"


class HMRCIntegrationException(Exception):
    """Exceptions to raise when sending requests to the HMRC Integration service."""


def send_licence(licence: Licence):
    url = f"{LITE_HMRC_INTEGRATION_URL}{SEND_LICENCE_ENDPOINT}"
    data = {"licence": HMRCIntegrationLicenceSerializer(licence).data}

    response = post(url, data, hawk_credentials=HAWK_CREDENTIALS, timeout=LITE_HMRC_REQUEST_TIMEOUT)

    if response.status_code != status.HTTP_201_CREATED:
        raise HMRCIntegrationException(
            f"An unexpected response was received when sending licence '{licence.id}' changes to HMRC Integration -> "
            f"status={response.status_code}, message={response.text}"
        )
