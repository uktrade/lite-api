from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import ExporterAuthentication
from goodstype.models import GoodsType
from goodstype.serializers import GoodsTypeSerializer


class GoodsTypeList(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request):
        """
        Gets list of all Goods Types
        """
        goods = GoodsType.objects.filter()
        serializer = GoodsTypeSerializer(goods, many=True)
        return JsonResponse(data={'goods': serializer.data},
                            )

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
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        """
        Gets a single Goods Type
        """
        good = GoodsType.objects.get(pk=pk)
        serializer = GoodsTypeSerializer(good)
        return JsonResponse(data={'good': serializer.data})
