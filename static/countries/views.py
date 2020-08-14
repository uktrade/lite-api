from django.http import JsonResponse
from rest_framework.generics import RetrieveAPIView
from rest_framework.views import APIView

from api.conf.authentication import HawkOnlyAuthentication
from static.countries.models import Country
from static.countries.serializers import CountrySerializer


class CountriesList(APIView):
    authentication_classes = (HawkOnlyAuthentication,)

    def get(self, request):
        countries = Country.exclude_special_countries.exclude(id__in=request.GET.getlist("exclude"))
        serializer = CountrySerializer(countries, many=True)
        return JsonResponse(data={"countries": serializer.data})


class CountryDetail(RetrieveAPIView):
    authentication_classes = (HawkOnlyAuthentication,)

    queryset = Country.objects.all()
    serializer_class = CountrySerializer
