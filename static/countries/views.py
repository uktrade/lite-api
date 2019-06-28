from django.http import JsonResponse
from rest_framework.views import APIView

from static.countries.models import Country
from static.countries.serializers import CountrySerializer


class CountriesList(APIView):
    def get(self, request):
        countries = Country.objects.all()
        serializer = CountrySerializer(countries, many=True)
        return JsonResponse(data={'countries': serializer.data})
