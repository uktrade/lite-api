from django.db.models import Q
from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination

from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.licences import models, enums
from api.licences.serializers import view_licence as serializers
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus


class LicencesListDW(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = serializers.LicenceListSerializer
    pagination_class = LimitOffsetPagination
    non_active_states = CaseStatus.objects.filter(status=CaseStatusEnum.SURRENDERED)

    queryset = (
        models.Licence.objects.exclude(Q(case__status__in=non_active_states) | Q(status=enums.LicenceStatus.DRAFT))
        .order_by("created_at")
        .reverse()
    )
