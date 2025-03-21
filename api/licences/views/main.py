from django.db.models import Q
from django.http import JsonResponse
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView, ListAPIView, RetrieveUpdateAPIView
from rest_framework import status

from api.cases.enums import CaseTypeSubTypeEnum, AdviceType, AdviceLevel
from api.cases.generated_documents.models import GeneratedCaseDocument
from api.cases.models import CaseType
from api.core.authentication import ExporterAuthentication, GovAuthentication
from api.core.constants import Roles
from api.core.decorators import authorised_govuser_roles, licence_is_editable
from api.licences.enums import LicenceStatus
from api.licences.models import Licence
from api.licences.serializers.view_licence import (
    ExporterLicenceViewSerializer,
    LicenceDetailsSerializer,
    NLRdocumentSerializer,
    LicenceListSerializer,
)
from api.organisations.libraries.get_organisation import get_request_user_organisation_id, get_request_user_organisation
from api.parties.enums import PartyType
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus


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
        end_user = self.request.GET.get("end_user")
        active_only = self.request.GET.get("active_only") == "True"

        licences = Licence.objects.filter(
            case__organisation_id=get_request_user_organisation_id(self.request),
        ).exclude(Q(status=LicenceStatus.DRAFT))

        # Apply filters
        if licence_type in [LicenceType.LICENCE, LicenceType.CLEARANCE]:
            licences = licences.filter(case__case_type__in=LicenceType.ids[licence_type])

        if reference:
            licences = licences.filter(
                Q(case__baseapplication__name__icontains=reference) | Q(case__reference_code__icontains=reference)
            )

        if clc:
            licences = licences.filter(
                Q(case__baseapplication__goods__good__control_list_entries__rating=clc)
            ).distinct()

        if end_user:
            licences = licences.filter(
                case__baseapplication__parties__party__name__icontains=end_user,
                case__baseapplication__parties__party__type=PartyType.END_USER,
            )

        if active_only:
            licences = licences.exclude(case__status__in=self.non_active_states)

        licences = licences.prefetch_related(
            "goods__good__good",
            "goods__good__control_list_entries",
        )

        return licences.order_by("created_at").reverse()


class ViewLicence(RetrieveAPIView):
    authentication_classes = (ExporterAuthentication,)
    serializer_class = ExporterLicenceViewSerializer

    def get_queryset(self):
        return Licence.objects.filter(case__organisation_id=get_request_user_organisation_id(self.request))


#
class LicenceDetails(RetrieveUpdateAPIView):
    # This is used to retrieve the details of the license based on id. ViewLicence is mainly used on exported side to get the
    # License(s) on the case.
    authentication_classes = (GovAuthentication,)
    serializer_class = LicenceDetailsSerializer
    queryset = Licence.objects.all()
    lookup_field = "pk"

    def dispatch(self, request, *args, **kwargs):
        if request.method not in ["PATCH", "GET"]:
            return JsonResponse(
                data={"errors": ["You are not authorised to perform this operation"]},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().dispatch(request, *args, **kwargs)

    @authorised_govuser_roles([Roles.INTERNAL_LU_SENIOR_MANAGER_ROLE_ID])
    @licence_is_editable()
    def patch(self, request, pk):
        return super().patch(request, pk)


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
