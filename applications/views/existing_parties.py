from rest_framework import generics

from applications.libraries.get_applications import get_application
from conf.authentication import ExporterAuthentication
from parties.models import Party
from parties.serializers import PartySerializer


class ExistingParties(generics.ListCreateAPIView):
    """
    Gets all existing parties for a given organisation (extracted from the application)
    in a paginated format.

    Allows additional get params to be passed to filter the parties.
    Also adds __contains to the get params to make the result set include partial matches
    i.e. name=Abc becomes name__contains=Abc when in filter.
    Country is filtered by name (i.e. United Kingdom)
    """

    authentication_classes = (ExporterAuthentication,)
    serializer_class = PartySerializer

    def get_queryset(self):
        params = {f"{key}__contains": value[0] for key, value in dict(self.request.GET).items()}
        # Rename country to country__name for filter
        if "country__contains" in params:
            params["country__name__contains"] = params.pop("country__contains")

        application_id = self.kwargs["pk"]
        application = get_application(application_id)
        return Party.objects.filter(organisation=application.organisation, **params)
