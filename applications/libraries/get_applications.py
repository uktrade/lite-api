from django.http import Http404

from applications.enums import ApplicationType
from applications.models import (
    BaseApplication,
    OpenApplication,
    StandardApplication,
    HmrcQuery,
)


def get_application(pk, organisation_id=None):
    kwargs = {}
    if organisation_id:
        kwargs["organisation_id"] = str(organisation_id)

    application_type = _get_application_type(pk)

    try:
        if application_type == ApplicationType.STANDARD_LICENCE:
            return StandardApplication.objects.get(pk=pk, **kwargs)
        elif application_type == ApplicationType.OPEN_LICENCE:
            return OpenApplication.objects.get(pk=pk, **kwargs)
        elif application_type == ApplicationType.HMRC_QUERY:
            return HmrcQuery.objects.get(pk=pk)
        else:
            raise NotImplementedError(f"get_application does not support this application type: {application_type}")
    except (
        StandardApplication.DoesNotExist,
        OpenApplication.DoesNotExist,
        HmrcQuery.DoesNotExist,
    ):
        raise Http404


def _get_application_type(pk):
    try:
        return BaseApplication.objects.values_list("application_type", flat=True).get(pk=pk)
    except BaseApplication.DoesNotExist:
        raise Http404
