from applications.models import BaseApplication, SiteOnApplication, ExternalLocationOnApplication
from conf.exceptions import NotFoundError
from organisations.models import Site


def get_site_by_pk(pk):
    try:
        return Site.objects.get(pk=pk)
    except Site.DoesNotExist:
        raise NotFoundError({'site': 'Site not found - ' + str(pk)})


def get_site_with_organisation(pk, organisation):
    try:
        site = Site.objects.get(pk=pk)

        if site.organisation.pk != organisation.pk:
            raise NotFoundError({'site': 'Site does not belong to organisation'})

        return site
    except Site.DoesNotExist:
        raise NotFoundError({'site': 'Site not found - ' + str(pk)})


def has_previous_sites(application: BaseApplication):
    return SiteOnApplication.objects.filter(application=application).exists()


def has_previous_external_locations(application: BaseApplication):
    return ExternalLocationOnApplication.objects.filter(application=application).exists()


def get_site_countries_on_application(application: BaseApplication):
    sites_on_application = SiteOnApplication.objects.filter(application=application)
    return [site_on_app.site.address.country for site_on_app in sites_on_application]


def get_external_location_countries_on_application(application: BaseApplication):
    ext_locs_on_app = ExternalLocationOnApplication.objects.filter(application=application)
    return [ext_loc_on_app.ext_loc.country for ext_loc_on_app in ext_locs_on_app]