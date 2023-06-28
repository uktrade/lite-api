from rest_framework import generics

from api.core.authentication import HawkOnlyAuthentication

from django.db.models.functions import Lower
from django.http import Http404
from django.urls import reverse
from django.views.generic.base import RedirectView

from .models import RegimeEntry
from .serializers import RegimeEntrySerializer


class RegimeEntriesListView(generics.ListAPIView):
    authentication_classes = (HawkOnlyAuthentication,)
    model = RegimeEntry
    pagination_class = None
    serializer_class = RegimeEntrySerializer
    queryset = RegimeEntry.objects.all()


class EntriesView(generics.ListAPIView):
    authentication_classes = (HawkOnlyAuthentication,)
    pagination_class = None
    serializer_class = RegimeEntrySerializer

    def get_queryset(self):
        regime_type = self.kwargs["regime_type"]

        regime_entries = (
            RegimeEntry.objects.select_related("subsection__regime")
            .annotate(regime_slug=Lower("subsection__regime__name"))
            .filter(
                regime_slug=regime_type,
            )
            .order_by("name")
        )

        if not regime_entries.exists():
            raise Http404

        return regime_entries


class MTCREntriesView(RedirectView):
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        return reverse(
            "staticdata:regimes:entries",
            kwargs={
                "regime_type": "mtcr",
            },
        )


class WassenaarEntriesView(RedirectView):
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        return reverse(
            "staticdata:regimes:entries",
            kwargs={
                "regime_type": "wassenaar",
            },
        )
