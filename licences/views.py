from django.db.models import Q, Count
from rest_framework.generics import ListCreateAPIView

from applications.models import CountryOnApplication
from cases.enums import CaseTypeSubTypeEnum, AdviceType
from cases.models import CaseType
from conf.authentication import ExporterAuthentication
from licences.models import Licence
from licences.serializers import LicenceListSerializer
from parties.enums import PartyType
from static.decisions.models import Decision
from static.statuses.enums import CaseStatusEnum
from static.statuses.models import CaseStatus


class LicenceType:
    LICENCE = "licence"
    CLEARANCE = "clearance"
    NLR = "nlr"

    ids = {
        LICENCE: CaseType.objects.filter(sub_type__in=CaseTypeSubTypeEnum.licence).values("id"),
        CLEARANCE: CaseType.objects.filter(sub_type__in=CaseTypeSubTypeEnum.mod).values("id"),
    }


class Licences(ListCreateAPIView):
    authentication_classes = (ExporterAuthentication,)
    serializer_class = LicenceListSerializer
    non_active_states = CaseStatus.objects.filter(status=CaseStatusEnum.SURRENDERED)

    def get_queryset(self):
        # Get params
        licence_type = self.request.GET.get("licence_type")
        reference = self.request.GET.get("reference")
        clc = self.request.GET.get("clc")
        country = self.request.GET.get("country")
        end_user = self.request.GET.get("end_user")
        active_only = self.request.GET.get("active_only") == "True"
        no_licence_required = Decision.objects.get(name=AdviceType.NO_LICENCE_REQUIRED)

        licences = Licence.objects.filter(application__organisation=self.request.user.organisation, is_complete=True)

        # Apply filters
        if licence_type in [LicenceType.LICENCE, LicenceType.CLEARANCE]:
            # Get all licences except those where the only decision is NLR
            licences = (
                licences.filter(application__case_type__in=LicenceType.ids[licence_type])
                .annotate(num_decisions=Count("decisions"))
                .exclude(decisions=no_licence_required, num_decisions=1)
            )
        elif licence_type == LicenceType.NLR:
            licences = licences.filter(decisions=no_licence_required)

        if reference:
            licences = licences.filter(
                Q(application__name__contains=reference) | Q(application__reference_code__contains=reference)
            )

        if clc:
            licences = licences.filter(
                Q(application__goods__good__control_list_entries__rating=clc)
                | Q(application__goods_type__control_list_entries__rating=clc)
            ).distinct()

        if country:
            licences = licences.filter(
                Q(application__parties__party__country_id=country, application__parties__party__type=PartyType.END_USER)
                | Q(
                    application__id__in=CountryOnApplication.objects.filter(country_id=country).values_list(
                        "application", flat=True
                    )
                )
            )

        if end_user:
            licences = licences.filter(
                application__parties__party__name__contains=end_user,
                application__parties__party__type=PartyType.END_USER,
            )

        if active_only:
            licences = licences.exclude(application__status__in=self.non_active_states)

        return licences.order_by("created_at").reverse()
