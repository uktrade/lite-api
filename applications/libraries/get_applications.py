from django.http import Http404

from applications.enums import ApplicationLicenceType
from applications.models import BaseApplication, OpenApplication, StandardApplication
from organisations.models import Organisation


def _add_submitted_filter(kwargs, submitted: bool):
    if submitted is not None:
        kwargs['submitted_at__isnull'] = not submitted


def _add_organisation_filter(kwargs, organisation):
    if organisation:
        if isinstance(organisation, Organisation):
            kwargs['organisation'] = organisation
        else:
            raise TypeError('object "organisation" provided is not an instance of Organisation model')


def get_base_applications(organisation=None, submitted=None):
    """
    If param organisation is None, all applications are returned
    If it is supplied, only applications for the specific organisation are returned

    If param submitted is None, all applications are returned
    If it is true (and consequently submitted_at__isnull is false), only submitted applications are returned
    If it is false (and consequently submitted_at__isnull is true), only draft applications are returned
    """
    kwargs = dict()

    _add_submitted_filter(kwargs, submitted)
    _add_organisation_filter(kwargs, organisation)

    applications = BaseApplication.objects.filter(**kwargs)

    return applications


def get_application(pk, organisation=None, submitted=None):
    kwargs = {}

    _add_submitted_filter(kwargs, submitted)
    _add_organisation_filter(kwargs, organisation)

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
        return BaseApplication.objects.get(pk=pk).licence_type
    except BaseApplication.DoesNotExist:
        raise Http404
