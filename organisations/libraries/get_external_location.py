from applications.models import BaseApplication, ExternalLocationOnApplication
from conf.exceptions import NotFoundError
from organisations.models import ExternalLocation


def get_location(pk, organisation=None):
    kwargs = {'pk': pk}

    if organisation:
        kwargs['organisation'] = organisation

    try:
        return ExternalLocation.objects.get(**kwargs)
    except ExternalLocation.DoesNotExist:
        raise NotFoundError({'external_location': 'External location not found - ' + str(pk)})


def has_previous_locations(application: BaseApplication):
    return ExternalLocationOnApplication.objects.filter(application=application).exists()
