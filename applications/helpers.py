from applications.enums import ApplicationType
from applications.models import BaseApplication, StandardApplication, OpenApplication, HmrcQuery
from applications.serializers.hmrc_query import HmrcQueryCreateSerializer, HmrcQueryViewSerializer
from applications.serializers.open_application import OpenApplicationCreateSerializer
from applications.serializers.serializers import OpenApplicationViewSerializer, StandardApplicationViewSerializer
from applications.serializers.standard_application import StandardApplicationCreateSerializer
from conf.exceptions import BadRequestError


def get_application_view_serializer(application: BaseApplication, many=False):
    if isinstance(application, StandardApplication):
        return StandardApplicationViewSerializer(application, many=many)
    elif isinstance(application, OpenApplication):
        return OpenApplicationViewSerializer(application, many=many)
    elif isinstance(application, HmrcQuery):
        return HmrcQueryViewSerializer(application, many=many)
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


def get_application_update_serializer(application_type):
    return None
