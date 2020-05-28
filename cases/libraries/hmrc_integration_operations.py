import conf.requests
from licences.models import Licence


class HMRCIntegrationException(Exception):
    """Exceptions to raise when sending requests to the HMRC Integration service."""


def send_licence_changes(licence: Licence):

    conf.requests.post()
