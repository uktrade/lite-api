from applications.models import BaseApplication, StandardApplication
from applications.serializers import StandardApplicationSerializer, OpenApplicationSerializer


def get_serializer_for_application(application: BaseApplication, many=False):
    if isinstance(application, StandardApplication):
        return StandardApplicationSerializer(application, many=many)
    else:
        return OpenApplicationSerializer(application, many=many)


def optional_str_to_bool(optional_string: str):
    if optional_string is None:
        return None
    elif optional_string == 'true':
        return True
    elif optional_string == 'false':
        return False
    else:
        raise ValueError('You provided ' + optional_string + ', while the allowed values are None, "true" or "false"')
