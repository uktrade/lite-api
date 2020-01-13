from django.http import JsonResponse
from rest_framework.views import APIView

from conf.authentication import GovAuthentication
from goodstype.helpers import get_goods_type
from goodstype.serializers import FullGoodsTypeSerializer


class GoodsTypeDetail(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Gets a single Goods Type
        """
        good = get_goods_type(pk=pk)
        serializer = FullGoodsTypeSerializer(good)
        return JsonResponse(data={"good": serializer.data})
