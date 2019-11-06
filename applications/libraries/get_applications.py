from django.http import Http404

from applications.enums import ApplicationLicenceType
from applications.models import BaseApplication, OpenApplication, StandardApplication


def get_application(pk, organisation_id=None):
    kwargs = {}
    if organisation_id:
        kwargs["organisation_id"] = str(organisation_id)

    licence_type = _get_application_licence_type(pk)

    try:
        if licence_type == ApplicationLicenceType.STANDARD_LICENCE:
            return StandardApplication.objects.get(pk=pk, **kwargs)
        else:
            return OpenApplication.objects.get(pk=pk, **kwargs)
    except (StandardApplication.DoesNotExist, OpenApplication.DoesNotExist):
        raise Http404


def _get_application_licence_type(pk):
    try:
        return BaseApplication.objects.values_list("licence_type", flat=True).get(pk=pk)
    except BaseApplication.DoesNotExist:
        raise Http404
