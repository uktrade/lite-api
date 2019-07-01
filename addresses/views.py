from django.http import JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from addresses.serializers import AddressSerializer


class Address(APIView):
    """
    Authenticate user
    """
    # TODO: remove address stuff
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        data = JSONParser().parse(request)
        address_serializer = AddressSerializer(data=data)
        if address_serializer.is_valid():
            return JsonResponse(data={'countries': address_serializer.data})
        else:
            return JsonResponse(data={'errors': address_serializer.errors})

