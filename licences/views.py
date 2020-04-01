from rest_framework.generics import ListCreateAPIView

from cases.enums import CaseTypeSubTypeEnum, AdviceType
from cases.models import CaseType
from conf.authentication import ExporterAuthentication
from licences.models import Licence
from licences.serializers import LicenceListSerializer


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

    def get_queryset(self):
        # Get params
        licence_type = self.request.GET.get("type", LicenceType.LICENCE)

        licences = Licence.objects.filter(application__organisation=self.request.user.organisation, is_complete=True)

        if licence_type in [LicenceType.LICENCE, LicenceType.CLEARANCE]:
            licences = licences.filter(application__case_type__in=LicenceType.ids[licence_type])

        return licences
