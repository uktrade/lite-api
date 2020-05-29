from rest_framework import status

from conf.requests import post
from conf.settings import LITE_HMRC_INTEGRATION_URL

HAWK_CREDENTIALS = "lite-api"
REQUEST_TIMEOUT = 5  # Maximum time, in seconds, to wait for a request to return a byte


class HMRCIntegrationException(Exception):
    """Exceptions to raise when sending requests to the HMRC Integration service."""


def send_licence(licence):
    url = LITE_HMRC_INTEGRATION_URL + "/mail/update-licence/"
    data = {"licence": {"id": str(licence.id)}}

    response = post(url, data, hawk_credentials=HAWK_CREDENTIALS, timeout=REQUEST_TIMEOUT)

    if response.status_code != status.HTTP_201_CREATED:
        raise HMRCIntegrationException(
            f"Received an unexpected response when sending licence '{licence.id}' changes to HMRC Integration -> "
            f"status={response.status_code}, message={response.text}"
        )
