import conf.requests
from conf.settings import LITE_HMRC_INTEGRATION_URL
from licences.models import Licence


class HMRCIntegrationException(Exception):
    """Exceptions to raise when sending requests to the HMRC Integration service."""


def send_licence_changes(licence: Licence):
    request_data = {"licence": {"id": str(licence.id)}}
    conf.requests.post(LITE_HMRC_INTEGRATION_URL + "/mail/update-licence/", request_data, {}, hawk_credentials=None)
