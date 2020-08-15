from django.http import Http404

from api.parties.models import Party
from api.staticdata.countries.models import Country


def get_destination(pk):
    try:
        destination = Country.objects.get(pk=pk)
    except Country.DoesNotExist:
        try:
            destination = Party.objects.get(pk=pk)
        except Party.DoesNotExist:
            raise Http404
    return destination
