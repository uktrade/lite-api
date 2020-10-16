from django.db.models import Q
from rest_framework import viewsets, pagination

from api.cases.enums import CaseTypeEnum
from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.licences.models import Licence
from api.licences.enums import LicenceStatus
from api.licences.serializers.view_licence import LicenceListSerializer
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus


class LicencesListDW(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = LicenceListSerializer
    pagination_class = pagination.LimitOffsetPagination
    non_active_states = CaseStatus.objects.filter(status=CaseStatusEnum.SURRENDERED)

    queryset = (
        # OGL's are always hidden as we don't treat them as a licence
        # and they shouldn't be viewed from this endpoint
        Licence.objects.exclude(
            Q(case__status__in=non_active_states)
            | Q(case__case_type__id__in=CaseTypeEnum.OPEN_GENERAL_LICENCE_IDS)
            | Q(status=LicenceStatus.DRAFT)
        ).order_by("created_at").reverse()
    )
