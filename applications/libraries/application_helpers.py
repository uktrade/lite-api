from applications.models import BaseApplication, StandardApplication
from applications.serializers import StandardApplicationSerializer, OpenApplicationSerializer


def get_serializer_for_application(application: BaseApplication, many=False):
    if isinstance(application, StandardApplication):
        return StandardApplicationSerializer(application, many=many)
    else:
        return OpenApplicationSerializer(application, many=many)
