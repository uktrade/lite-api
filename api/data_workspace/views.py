from django.db.models import Q
from rest_framework import viewsets

from api.cases.enums import CaseTypeEnum
from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.licences import models
from api.licences.enums import LicenceStatus
from api.licences.serializers.view_licence import LicenceListSerializer
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus


class LicencesListDW(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = LicenceListSerializer
    non_active_states = CaseStatus.objects.filter(status=CaseStatusEnum.SURRENDERED)

    def get_queryset(self):
        # OGL's are always hidden as we don't treat them as a licence
        # and they shouldn't be viewed from this endpoint
        licences = models.Licence.objects.exclude(
            Q(case__status__in=self.non_active_states)
            | Q(case__case_type__id__in=CaseTypeEnum.OPEN_GENERAL_LICENCE_IDS)
            | Q(status=LicenceStatus.DRAFT)
        )

        return licences.order_by("created_at").reverse()
