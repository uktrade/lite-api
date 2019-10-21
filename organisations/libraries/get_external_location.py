from applications.models import BaseApplication, ExternalLocationOnApplication
from conf.exceptions import NotFoundError
from organisations.models import ExternalLocation


def get_external_location(pk, organisation=None):
    kwargs = {'pk': pk}

    if organisation:
        kwargs['organisation'] = organisation

    try:
        return ExternalLocation.objects.get(**kwargs)
    except ExternalLocation.DoesNotExist:
        raise NotFoundError({'external_location': 'External location not found - ' + str(pk)})


def has_previous_external_locations(application: BaseApplication):
    return ExternalLocationOnApplication.objects.filter(application=application).exists()


def get_external_location_countries_on_application(application: BaseApplication):
    external_locations = ExternalLocationOnApplication.objects.filter(application=application)
    return [external_location.ext_loc.country for external_location in external_locations]
