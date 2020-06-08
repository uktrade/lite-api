from common.cache import lite_cache, Key
from static.countries.models import Country
from static.countries.serializers import CountrySerializer


@lite_cache(Key.COUNTRIES_LIST)
def get_countries_list():
    countries = Country.objects.all()
    serializer = CountrySerializer(countries, many=True)
    return serializer.data
