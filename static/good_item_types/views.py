from django.http import JsonResponse
from rest_framework.views import APIView

from goods.enums import ItemType


class GoodItemTypes(APIView):
    def get(self, request):
        return JsonResponse(data={"item_types": {choice[0]: choice[1] for choice in ItemType.choices}})
