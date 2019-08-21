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
