from conf.exceptions import NotFoundError
from static.countries.models import Country


def get_country(pk):
    try:
        return Country.objects.get(pk=pk)
    except Country.DoesNotExist:
        raise NotFoundError({"country": "Country not found - " + str(pk)})
