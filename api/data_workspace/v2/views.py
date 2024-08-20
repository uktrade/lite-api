from rest_framework import viewsets
from rest_framework.generics import ListAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.settings import api_settings

from rest_framework_csv.renderers import PaginatedCSVRenderer

from api.applications.models import StandardApplication
from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.data_workspace.v2.serializers import (
    LicenceDecisionSerializer,
    LicenceDecisionTypeSerializer,
    LicenceStatusSerializer,
    SIELApplicationSerializer,
)
from api.licences.enums import (
    LicenceDecisionType,
    LicenceStatus,
)
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status


class LicenceStatusesListView(viewsets.GenericViewSet, ListAPIView):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    pagination_class = LimitOffsetPagination
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (PaginatedCSVRenderer,)
    serializer_class = LicenceStatusSerializer

    def get_queryset(self):
        return LicenceStatus.all()


class LicenceDecisionTypesListView(viewsets.GenericViewSet, ListAPIView):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    pagination_class = LimitOffsetPagination
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (PaginatedCSVRenderer,)
    serializer_class = LicenceDecisionTypeSerializer

    def get_queryset(self):
        return LicenceDecisionType.all()


class SIELApplicationsListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    pagination_class = LimitOffsetPagination
    queryset = StandardApplication.objects.filter(amendment__isnull=True).exclude(submitted_at__isnull=True)
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (PaginatedCSVRenderer,)
    serializer_class = SIELApplicationSerializer


class LicenceDecisionsListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    pagination_class = LimitOffsetPagination
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (PaginatedCSVRenderer,)
    serializer_class = LicenceDecisionSerializer

    def get_queryset(self):
        withdrawn_status = get_case_status_by_status(CaseStatusEnum.WITHDRAWN)
        return StandardApplication.objects.filter(
            amendment__isnull=True,
            status=withdrawn_status,
        ).exclude(submitted_at__isnull=True)
