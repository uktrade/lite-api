from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.status import HTTP_200_OK

from api.conf.authentication import SharedAuthentication
from api.static.trade_control.enums import TradeControlProductCategory, TradeControlActivity


class Activities(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request):
        activities = [{"key": key, "value": value} for key, value in TradeControlActivity.choices]
        return JsonResponse(data={"activities": activities}, status=HTTP_200_OK)


class ProductCategories(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request):
        product_categories = [{"key": key, "value": value} for key, value in TradeControlProductCategory.choices]
        return JsonResponse(data={"product_categories": product_categories}, status=HTTP_200_OK)
