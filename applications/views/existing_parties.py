from django.db.models import Window, F
from django.db.models.functions import FirstValue
from rest_framework import generics

from applications.libraries.get_applications import get_application
from conf.authentication import ExporterAuthentication
from parties.models import Party
from parties.serializers import PartySerializer


class ExistingParties(generics.ListCreateAPIView):
    """
    Gets de-duplicated existing parties for a given organisation (extracted from the application)
    in a paginated format, where duplicate parties are parties that are copies of one another
    with the same name (i.e. the copy's name hasn't been changed from the original's)

    Allows additional get params to be passed to filter the parties.
    Also adds __contains to the get params to make the result set include partial matches
    i.e. name=Abc becomes name__contains=Abc when in filter.
    Country is filtered by name (i.e. United Kingdom)
    """

    authentication_classes = (ExporterAuthentication,)
    serializer_class = PartySerializer

    def get_queryset(self):
        # Assemble the supplied filters, ready to be used in querysets below
        params = {f"{key}__contains": value[0] for key, value in dict(self.request.GET).items()}
        # Rename country to country__name for filter
        if "country__contains" in params:
            params["country__name__contains"] = params.pop("country__contains")

        application_id = self.kwargs["pk"]
        application = get_application(application_id)

        # Stage 1: Build a query for uncopied parties, i.e. parties that are not copies of other
        # parties and have never been copied themselves
        party_copy_of_ids = Party.objects.filter(copy_of_id__isnull=False).values("copy_of_id").distinct()
        uncopied_parties = Party.objects.filter(
            organisation=application.organisation, copy_of_id__isnull=True, **params
        ).exclude(id__in=party_copy_of_ids)

        # Stage 2: Build a query set using a Django window function to find the most recent parties that are copies.
        # Essentially, we group copied parties by name and copy_of_id and for each grouping, get the id
        # of the newest party in the group.  Then use that set of ids to get the corresponding list of parties
        copied_party_ids = (
            Party.objects.filter(organisation=application.organisation, copy_of_id__isnull=False, **params)
            .annotate(
                first_party_id=Window(
                    expression=FirstValue("id"), partition_by=["name", "copy_of_id"], order_by=F("created_at").desc(),
                )
            )
            .values_list("first_party_id")
            .distinct()
        )
        copied_parties = Party.objects.filter(id__in=copied_party_ids)

        # Return the combined results from stages 1 and 2 above
        return uncopied_parties.union(copied_parties)
