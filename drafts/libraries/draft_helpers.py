from applications.enums import ApplicationLicenceType
from applications.models import AbstractApplication, StandardApplication
from applications.serializers import StandardApplicationSerializer, OpenApplicationSerializer


def get_serializer_for_draft(draft: AbstractApplication, many=False):
    if draft.licence_type == ApplicationLicenceType.STANDARD_LICENCE:
        return StandardApplicationSerializer(draft, many=many)
    else:
        return OpenApplicationSerializer(draft, many=many)
