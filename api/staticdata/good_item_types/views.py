from django.http import JsonResponse
from rest_framework.views import APIView

from api.core.authentication import SharedAuthentication
from api.goods.enums import ItemType


class GoodItemTypes(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request):
        return JsonResponse(data={"item_types": {choice[0]: choice[1] for choice in ItemType.choices}})
