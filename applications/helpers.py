from applications.enums import ApplicationType
from applications.models import BaseApplication
from applications.serializers.hmrc_query import HmrcQueryCreateSerializer, HmrcQueryViewSerializer, \
    HmrcQueryUpdateSerializer
from applications.serializers.open_application import OpenApplicationCreateSerializer, OpenApplicationUpdateSerializer, \
    OpenApplicationViewSerializer
from applications.serializers.standard_application import StandardApplicationCreateSerializer, \
    StandardApplicationUpdateSerializer, StandardApplicationViewSerializer
from conf.exceptions import BadRequestError


def get_application_view_serializer(application: BaseApplication):
    if application.application_type == ApplicationType.STANDARD_LICENCE:
        return StandardApplicationViewSerializer
    elif application.application_type == ApplicationType.OPEN_LICENCE:
        return OpenApplicationViewSerializer
    elif application.application_type == ApplicationType.HMRC_QUERY:
        return HmrcQueryViewSerializer
    else:
        raise BadRequestError({'errors': '??? todo'})  # TODO


def get_application_create_serializer(application_type):
    if application_type == ApplicationType.STANDARD_LICENCE:
        return StandardApplicationCreateSerializer
    elif application_type == ApplicationType.OPEN_LICENCE:
        return OpenApplicationCreateSerializer
    elif application_type == ApplicationType.HMRC_QUERY:
        return HmrcQueryCreateSerializer
    else:
        raise BadRequestError({'errors': f'Application type: {application_type} is not supported'})


def get_application_update_serializer(application: BaseApplication):
    if application.application_type == ApplicationType.STANDARD_LICENCE:
        return StandardApplicationUpdateSerializer
    elif application.application_type == ApplicationType.OPEN_LICENCE:
        return OpenApplicationUpdateSerializer
    elif application.application_type == ApplicationType.HMRC_QUERY:
        return HmrcQueryUpdateSerializer
    else:
        raise BadRequestError({'errors': '??? todo'})  # TODO
