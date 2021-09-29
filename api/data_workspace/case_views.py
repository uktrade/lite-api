from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination

from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.cases.models import CaseAssignment, CaseAssignmentSla, CaseType, CaseQueue, EcjuQuery, DepartmentSla
from api.cases.serializers import (
    CaseAssignmentSlaSerializer,
    CaseTypeSerializer,
    CaseQueueSerializer,
    CaseDepartmentSerializer,
)
from api.data_workspace.serializers import (
    EcjuQuerySerializer,
    CaseAssignmentSerializer,
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


class CaseDepartmentList(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = CaseDepartmentSerializer
    pagination_class = LimitOffsetPagination
    queryset = DepartmentSla.objects.all()


class EcjuQueryList(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = EcjuQuerySerializer
    pagination_class = LimitOffsetPagination
    queryset = EcjuQuery.objects.all().order_by("id")
