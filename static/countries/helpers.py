from django.http import Http404

from static.countries.models import Country


def get_country(pk):
    try:
        return Country.objects.get(pk=pk)
    except Country.DoesNotExist:
        raise Http404
