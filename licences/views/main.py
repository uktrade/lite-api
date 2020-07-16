from django.db.models import Q
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView, ListAPIView

from applications.models import CountryOnApplication
from cases.enums import CaseTypeSubTypeEnum, AdviceType, AdviceLevel
from cases.generated_documents.models import GeneratedCaseDocument
from cases.models import CaseType
from conf.authentication import ExporterAuthentication
from licences.enums import LicenceStatus
from licences.models import Licence
from licences.serializers.view_licence import LicenceSerializer, NLRdocumentSerializer, LicenceListSerializer
from organisations.libraries.get_organisation import get_request_user_organisation_id, get_request_user_organisation
from parties.enums import PartyType
from static.statuses.enums import CaseStatusEnum
from static.statuses.models import CaseStatus


class LicenceType:
    LICENCE = "licence"
    CLEARANCE = "clearance"

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

        licences = Licence.objects.filter(
            application__organisation_id=get_request_user_organisation_id(self.request),
        ).exclude(status=LicenceStatus.DRAFT)

        # Apply filters
        if licence_type in [LicenceType.LICENCE, LicenceType.CLEARANCE]:
            licences = licences.filter(application__case_type__in=LicenceType.ids[licence_type])

        if reference:
            licences = licences.filter(
                Q(application__name__icontains=reference) | Q(application__reference_code__icontains=reference)
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
                application__parties__party__name__icontains=end_user,
                application__parties__party__type=PartyType.END_USER,
            )

        if active_only:
            licences = licences.exclude(application__status__in=self.non_active_states)

        return licences.order_by("created_at").reverse()


class ViewLicence(RetrieveAPIView):
    authentication_classes = (ExporterAuthentication,)
    serializer_class = LicenceSerializer

    def get_queryset(self):
        return Licence.objects.filter(application__organisation_id=get_request_user_organisation_id(self.request))


class NLRs(ListAPIView):
    # TODO: using the NLRdocumentSerializer creates multiple queries for each result,
    #  query count can be cut down in future
    authentication_classes = (ExporterAuthentication,)
    serializer_class = NLRdocumentSerializer

    def get_queryset(self):
        organisation = get_request_user_organisation(self.request)
        documents = GeneratedCaseDocument.objects.select_related("case").filter(
            advice_type=AdviceType.NO_LICENCE_REQUIRED, case__organisation=organisation
        )

        reference = self.request.GET.get("reference")
        clc = self.request.GET.get("clc")
        country = self.request.GET.get("country")
        end_user = self.request.GET.get("end_user")

        if reference:
            documents = documents.filter(case__reference_code__contains=reference)

        if clc:
            documents = documents.filter(
                case__advice__good__control_list_entries__rating=clc,
                case__advice__level=AdviceLevel.FINAL,
                case__advice__type=AdviceType.NO_LICENCE_REQUIRED,
            )

        if country:
            documents = documents.filter(case__baseapplication__parties__party__country=country)

        if end_user:
            documents = documents.filter(case__baseapplication__parties__party__name__contains=end_user)

        return documents.distinct()
