from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import ExporterAuthentication, SharedAuthentication
from goodstype.helpers import get_goods_type
from goodstype.models import GoodsType
from goodstype.serializers import GoodsTypeSerializer, FullGoodsTypeSerializer
from static.countries.helpers import get_country
from users.models import GovUser


class GoodsTypeList(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request):
        """
        Gets list of all Goods Types
        """
        goods = GoodsType.objects.all()
        serializer = GoodsTypeSerializer(goods, many=True)
        return JsonResponse(data={'goods': serializer.data},)

    def post(self, request):
        """
        Posts Goods Types
        """
        data = JSONParser().parse(request)
        serializer = GoodsTypeSerializer(data=data)

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
        good = GoodsType.objects.get(pk=pk)
        if isinstance(request.user, GovUser):
            serializer = FullGoodsTypeSerializer(good)
        else:
            serializer = GoodsTypeSerializer(good)
        return JsonResponse(data={'good': serializer.data})


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

        # validate request data
        for pk in data:
            get_goods_type(pk)
            for country_code in data.get(pk):
                get_country(country_code)

        # persist
        for pk in data:
            good = get_goods_type(pk)
            good.countries.set(data.get(pk))

        return JsonResponse(data=data, status=status.HTTP_200_OK)
