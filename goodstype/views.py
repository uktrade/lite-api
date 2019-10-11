from django.db import transaction
from django.http import JsonResponse, Http404, HttpResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from applications.enums import ApplicationLicenceType
from conf.authentication import ExporterAuthentication, SharedAuthentication
from conf.decorators import only_application_type
from goodstype.helpers import get_goods_type
from goodstype.models import GoodsType
from goodstype.serializers import GoodsTypeSerializer, FullGoodsTypeSerializer
from static.countries.models import Country
from users.models import GovUser


class GoodsTypeList(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request):
        """
        Gets list of all Goods Types
        """
        goods = GoodsType.objects.all()
        serializer = GoodsTypeSerializer(goods, many=True)
        return JsonResponse(data={'goods': serializer.data}, )

    @only_application_type(ApplicationLicenceType.OPEN_LICENCE, return_draft=False)
    def post(self, request):
        """
        Posts Goods Types
        """
        serializer = GoodsTypeSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'good': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class GoodsTypeDetail(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request, pk):
        """
        Gets a single Goods Type
        """
        try:
            good = GoodsType.objects.get(pk=pk)
        except GoodsType.DoesNotExist as e:
            return JsonResponse(data={'errors': str(e)}, status=status.HTTP_404_NOT_FOUND)

        if isinstance(request.user, GovUser):
            serializer = FullGoodsTypeSerializer(good)
        else:
            serializer = GoodsTypeSerializer(good)
        return JsonResponse(data={'good': serializer.data})

    def delete(self, request, pk):
        try:
            GoodsType.objects.get(pk=pk).delete()
        except GoodsType.DoesNotExist:
            return HttpResponse(status=status.HTTP_404_NOT_FOUND)

        return HttpResponse(status=status.HTTP_204_NO_CONTENT)


class Countries(APIView):
    """
    Sets countries on goodstypes
    """
    authentication_classes = (ExporterAuthentication,)

    @transaction.atomic
    def put(self, request):
        """
        Accepts {goodstype_id: [country_id, country_id], goodstype_id: [etc...], etc...}
        """
        data = JSONParser().parse(request)

        for good, countries in data.items():
            good = get_goods_type(good)
            if not Country.objects.filter(pk__in=countries).count() == len(countries):
                raise Http404

            good.countries.set(countries)

        return JsonResponse(data=data, status=status.HTTP_200_OK)
