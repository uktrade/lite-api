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


def get_site_countries_on_application(application: BaseApplication):
    sites_on_application = SiteOnApplication.objects.filter(application=application)
    return [site_on_app.site.address.country for site_on_app in sites_on_application]
