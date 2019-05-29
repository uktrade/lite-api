from django.http import Http404

from organisations.models import ExternalSite


def get_external_site_by_pk(pk):
    try:
        return ExternalSite.objects.get(pk=pk)
    except ExternalSite.DoesNotExist:
        raise Http404


def get_external_site_with_organisation(pk, organisation):
    try:
        external_site = ExternalSite.objects.get(pk=pk)

        if external_site.organisation.pk != organisation.pk:
            raise Http404

        return external_site
    except ExternalSite.DoesNotExist:
        raise Http404
