from django.http import JsonResponse
from rest_framework.views import APIView

from api.core.authentication import SharedAuthentication
from api.applications.enums import F680ClearanceChoices


class F680ClearanceTypesView(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request):
        clearance_types = {key: value for key, value in F680ClearanceChoices.choices}
        return JsonResponse(data={"types": clearance_types})
