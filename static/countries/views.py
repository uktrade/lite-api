from django.http import JsonResponse
from rest_framework.generics import RetrieveAPIView
from rest_framework.views import APIView

from conf.authentication import HawkOnlyAuthentication
from static.countries.models import Country
from static.countries.serializers import CountrySerializer
from static.countries.service import get_countries_list


class CountriesList(APIView):
    authentication_classes = (HawkOnlyAuthentication,)

    def get(self, request):
        countries = get_countries_list()
        excluded_countries = request.GET.getlist("exclude")
        if excluded_countries:
            countries = list(filter(lambda x: x["id"] not in excluded_countries, countries))
        return JsonResponse(data={"countries": countries})


class CountryDetail(RetrieveAPIView):
    authentication_classes = (HawkOnlyAuthentication,)

    queryset = Country.objects.all()
    serializer_class = CountrySerializer
