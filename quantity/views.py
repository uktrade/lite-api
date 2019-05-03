import json

from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from quantity.units import Units


class UnitsList(APIView):
    # authentication_classes = (PkAuthentication,)

    def get(self, request):
        # unit_choices = [u for u in Units]

        unit_choices = {key: str(value) for key, value in Units.__dict__.items()
                        if not key.startswith('_') and not callable(key)}
        # for key, value in Units.__dict__.items():
        #     if not key.startswith('_') and not callable(key):
        #         # print(type(value))
        #         print(key, value)
        #         print(Units.__getattr__(key))

        # print(unit_choices)
        # print(Units.NAR)
        #
        # key = 'NAR'
        # attrib_value = Units.__getattr__(key)
        #
        # print(attrib_value)

        json_data = json.dumps(unit_choices)
        return JsonResponse(data=unit_choices,
                            status=status.HTTP_200_OK, safe=False)
