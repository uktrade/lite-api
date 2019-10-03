from applications.models import BaseApplication, StandardApplication
from applications.serializers import StandardApplicationSerializer, OpenApplicationSerializer


def get_serializer_for_application(draft: BaseApplication, many=False):
    if isinstance(draft, StandardApplication):
        return StandardApplicationSerializer(draft, many=many)
    else:
        return OpenApplicationSerializer(draft, many=many)
