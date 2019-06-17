from django.http import JsonResponse, Http404
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView
from conf.authentication import PkAuthentication

from goodstype.models import GoodsType
from goodstype.serializers import GoodsTypeSerializer


class GoodsTypeList(APIView):
    authentication_classes = (PkAuthentication,)

    def get(self, request):
        description = request.GET.get('description', '')
        goods = GoodsType.objects.filter()
        serializer = GoodsTypeSerializer(goods, many=True)
        return JsonResponse(data={'goods': serializer.data},
                            safe=False)

    def post(self, request):
        data = JSONParser().parse(request)


        serializer = GoodsTypeSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'good': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class GoodsTypeDetail(APIView):
    authentication_classes = (PkAuthentication,)

    def get(self, request, pk):
        good = GoodsType.objects.get(pk=pk)

        serializer = GoodsTypeSerializer(good)
        return JsonResponse(data={'good': serializer.data})
