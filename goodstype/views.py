from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from conf.authentication import GovAuthentication
from goodstype.helpers import get_goods_type
from goodstype.models import GoodsType
from goodstype.serializers import GoodsTypeSerializer, FullGoodsTypeSerializer


class GoodsTypeList(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request):
        """
        Gets list of all Goods Types
        """
        goods = GoodsType.objects.all()
        serializer = GoodsTypeSerializer(goods, many=True)
        return JsonResponse(data={'goods': serializer.data}, status=status.HTTP_200_OK)


class GoodsTypeDetail(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Gets a single Goods Type
        """
        good = get_goods_type(pk=pk)
        serializer = FullGoodsTypeSerializer(good)
        return JsonResponse(data={'good': serializer.data})
