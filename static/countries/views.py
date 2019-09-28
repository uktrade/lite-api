from rest_framework.views import APIView

from conf.serializers import response_serializer
from static.countries.models import Country
from static.countries.serializers import CountrySerializer


class CountriesList(APIView):
    def get(self, request):
        countries = Country.objects.all()
        return response_serializer(CountrySerializer, obj=countries, many=True, response_name='countries')
