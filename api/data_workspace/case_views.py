from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination

from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.cases.models import CaseAssignmentSla, CaseType, CaseQueue
from api.cases.serializers import (
    CaseAssignmentSlaSerializer,
    CaseTypeSerializer,
    CaseQueueSerializer,
)


class CaseAssignmentSlaList(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = CaseAssignmentSlaSerializer
    pagination_class = LimitOffsetPagination
    queryset = CaseAssignmentSla.objects.all()


class CaseTypeList(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = CaseTypeSerializer
    pagination_class = LimitOffsetPagination
    queryset = CaseType.objects.all()


class CaseQueueList(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = CaseQueueSerializer
    pagination_class = LimitOffsetPagination
    queryset = CaseQueue.objects.all()
