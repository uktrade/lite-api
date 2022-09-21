from django.http import JsonResponse

from rest_framework.views import APIView

from api.core.authentication import HawkOnlyAuthentication


class MTCREntriesView(APIView):
    authentication_classes = (HawkOnlyAuthentication,)

    def get(self, request):
        return JsonResponse(data={"entries": [["MTCR1", "MTCR1"]]})
