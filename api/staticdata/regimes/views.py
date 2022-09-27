from rest_framework import generics

from api.core.authentication import HawkOnlyAuthentication

from .enums import RegimesEnum
from .models import RegimeEntry
from .serializers import RegimeEntrySerializer


class MTCREntriesView(generics.ListAPIView):
    authentication_classes = (HawkOnlyAuthentication,)
    pagination_class = None
    queryset = RegimeEntry.objects.filter(subsection__regime=RegimesEnum.MTCR).order_by("name")
    serializer_class = RegimeEntrySerializer
