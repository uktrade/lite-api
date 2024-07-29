from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination

from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.cases.models import CaseAssignment, CaseAssignmentSLA, CaseType, CaseQueue, EcjuQuery, DepartmentSLA
from api.cases.serializers import (
    CaseAssignmentSLASerializer,
    CaseTypeSerializer,
    CaseQueueSerializer,
)
from api.data_workspace.serializers import (
    EcjuQuerySerializer,
    CaseAssignmentSerializer,
    DepartmentSLASerializer,
)


class CaseAssignmentList(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = CaseAssignmentSerializer
    pagination_class = LimitOffsetPagination
    queryset = CaseAssignment.objects.all().order_by("id")


class CaseAssignmentSLAList(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = CaseAssignmentSLASerializer
    pagination_class = LimitOffsetPagination
    queryset = CaseAssignmentSLA.objects.all()


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
    serializer_class = DepartmentSLASerializer
    pagination_class = LimitOffsetPagination
    queryset = DepartmentSLA.objects.all()


class EcjuQueryList(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = EcjuQuerySerializer
    pagination_class = LimitOffsetPagination
    queryset = EcjuQuery.objects.all().order_by("id")
