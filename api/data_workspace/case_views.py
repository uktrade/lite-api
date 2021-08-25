from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination

from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.cases.models import CaseAssignment, CaseAssignmentSla, CaseType, CaseQueue
from api.cases.serializers import (
    CaseAssignmentSerializer,
    CaseAssignmentSlaSerializer,
    CaseTypeSerializer,
    CaseQueueSerializer,
)


class CaseAssignmentList(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = CaseAssignmentSerializer
    pagination_class = LimitOffsetPagination
    queryset = CaseAssignment.objects.all().order_by("id")


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
