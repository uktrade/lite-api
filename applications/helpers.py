from applications.enums import ApplicationType
from applications.serializers.hmrc import HmrcQueryCreateSerializer
from applications.serializers.open_application import OpenApplicationCreateSerializer
from applications.serializers.standard_application import StandardApplicationCreateSerializer
from conf.exceptions import BadRequestError


def get_application_create_serializer(application_type):
    if application_type == ApplicationType.STANDARD_LICENCE:
        return StandardApplicationCreateSerializer
    elif application_type == ApplicationType.OPEN_LICENCE:
        return OpenApplicationCreateSerializer
    elif application_type == ApplicationType.HMRC_QUERY:
        return HmrcQueryCreateSerializer
    else:
        raise BadRequestError({'errors': f'Application type: {application_type} is not supported'})


def get_application_update_serializer():
    return None


def get_application__serializer():
    return None
