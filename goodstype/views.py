from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import ExporterAuthentication, SharedAuthentication, GovAuthentication
from goodstype.helpers import get_goods_type
from goodstype.models import GoodsType
from goodstype.serializers import GoodsTypeSerializer, FullGoodsTypeSerializer
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


class GoodsTypeActivity(APIView):
    authentication_classes = (GovAuthentication,)
    """
    Retrieves all activity related to a good
    * Good Updates
    * Good Notes
    * ECJU Queries
    """

    def get(self, request, pk):
        good = get_goods_type(pk)

        # TODO
        # version_records = Version.objects.filter(Q(object_id=good.pk))
        # activity = []
        # for version in version_records:
        #     activity_item = convert_good_reversion_to_activity(version, good)
        #     if activity_item:
        #         activity.append(activity_item)
        #
        # # Sort the activity based on date (newest first)
        # activity.sort(key=lambda x: x['date'], reverse=True)

        return JsonResponse(data={'activity': {}})
