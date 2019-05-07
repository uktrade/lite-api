from django.http import Http404

from organisations.models import Site


def get_site_by_ok(pk):
    try:
        return Site.objects.get(pk=pk)
    except Site.DoesNotExist:
        raise Http404


def get_site_with_organisation(pk, organisation):
    try:
        site = Site.objects.get(pk=pk)

        if site.organisation.pk != organisation.pk:
            raise Http404

        return site
    except Site.DoesNotExist:
        raise Http404
