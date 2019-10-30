from applications.models import BaseApplication, SiteOnApplication
from conf.exceptions import NotFoundError
from organisations.models import Site


def get_site(pk, organisation=None):
    kwargs = {'pk': pk}

    if organisation:
        kwargs['organisation'] = organisation

    try:
        return Site.objects.get(**kwargs)
    except Site.DoesNotExist:
        raise NotFoundError({'site': 'Site not found - ' + str(pk)})


def has_previous_sites(application: BaseApplication):
    return SiteOnApplication.objects.filter(application=application).exists()
