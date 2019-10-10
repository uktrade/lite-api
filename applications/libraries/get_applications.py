from django.http import Http404

from applications.enums import ApplicationLicenceType
from applications.models import BaseApplication, OpenApplication, StandardApplication


def _add_submitted_filter(kwargs, submitted: bool):
    if submitted is not None:
        kwargs['submitted_at__isnull'] = not submitted


def _add_organisation_filter(kwargs, organisation_id):
    if organisation_id:
        kwargs['organisation_id'] = str(organisation_id)


def _get_filters(organisation_id=None, submitted=None):
    kwargs = {}

    _add_submitted_filter(kwargs, submitted)
    _add_organisation_filter(kwargs, organisation_id)

    return kwargs


def get_base_applications(organisation_id=None, submitted=None):
    kwargs = _get_filters(organisation_id, submitted)

    applications = BaseApplication.objects.filter(**kwargs)

    return applications


def get_application(pk, organisation_id=None, submitted=None):
    kwargs = _get_filters(organisation_id, submitted)
    licence_type = get_application_licence_type(pk)

    try:
        if licence_type == ApplicationLicenceType.STANDARD_LICENCE:
            return StandardApplication.objects.get(pk=pk, **kwargs)
        else:
            return OpenApplication.objects.get(pk=pk, **kwargs)
    except (StandardApplication.DoesNotExist, OpenApplication.DoesNotExist):
        raise Http404


def get_application_licence_type(pk):
    try:
        return BaseApplication.objects.values_list('licence_type', flat=True).get(pk=pk)
    except BaseApplication.DoesNotExist:
        raise Http404
