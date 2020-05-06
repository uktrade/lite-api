from django.http import JsonResponse
from rest_framework.generics import RetrieveAPIView
from rest_framework.views import APIView

from conf.authentication import SharedAuthentication
from static.countries.models import Country
from static.countries.serializers import CountrySerializer


class CountriesList(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request):
        countries = Country.objects.exclude(id__in=request.GET.getlist("exclude"))
        serializer = CountrySerializer(countries, many=True)
        return JsonResponse(data={"countries": serializer.data})


class CountryDetail(RetrieveAPIView):
    authentication_classes = (SharedAuthentication,)

    queryset = Country.objects.all()
    serializer_class = CountrySerializer
