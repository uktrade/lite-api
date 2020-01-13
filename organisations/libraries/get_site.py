from applications.models import BaseApplication, SiteOnApplication
from conf.exceptions import NotFoundError
from organisations.models import Site


def get_site(pk, organisation) -> Site:
    try:
        return Site.objects.get(pk=pk, organisation=organisation)
    except Site.DoesNotExist:
        raise NotFoundError({"site": "Site not found - " + str(pk)})


def has_previous_sites(application: BaseApplication):
    return SiteOnApplication.objects.filter(application=application).exists()
