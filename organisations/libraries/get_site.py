from django.http import Http404

from organisations.models import Site


def get_site_by_organisation(site_pk, org_pk):
    try:
        site = Site.objects.get(pk=site_pk)

        if site.organisation.pk != org_pk:
            raise Http404

        return site
    except Site.DoesNotExist:
        raise Http404
