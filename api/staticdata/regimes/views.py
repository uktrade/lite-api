from rest_framework import generics

from api.core.authentication import HawkOnlyAuthentication

from .enums import RegimesEnum
from .models import RegimeEntry
from .serializers import RegimeEntrySerializer


class BaseEntriesView(generics.ListAPIView):
    authentication_classes = (HawkOnlyAuthentication,)
    pagination_class = None
    serializer_class = RegimeEntrySerializer

    def get_queryset(self):
        return RegimeEntry.objects.filter(subsection__regime=self.regime_type).order_by("name")


class MTCREntriesView(BaseEntriesView):
    regime_type = RegimesEnum.MTCR


class WassenaarEntriesView(BaseEntriesView):
    regime_type = RegimesEnum.WASSENAAR
