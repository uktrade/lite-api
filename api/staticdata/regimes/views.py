from django.http import JsonResponse

from rest_framework.views import APIView

from api.core.authentication import HawkOnlyAuthentication

from .enums import RegimesEnum
from .models import RegimeEntry


class MTCREntriesView(APIView):
    authentication_classes = (HawkOnlyAuthentication,)

    def get(self, request):
        entries = (
            RegimeEntry.objects.filter(subsection__regime=RegimesEnum.MTCR).order_by("name").values_list("pk", "name")
        )

        return JsonResponse(
            data={
                "entries": list(entries),
            }
        )
