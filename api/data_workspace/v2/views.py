import datetime

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.settings import api_settings

from rest_framework_csv.renderers import (
    CSVRenderer,
    PaginatedCSVRenderer,
)

from api.applications.models import StandardApplication
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.models import EcjuQuery
from api.common.dates import (
    is_bank_holiday,
    is_weekend,
)
from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.data_workspace.v2.serializers import (
    ApplicationSerializer,
    NonWorkingDaySerializer,
    RFISerializer,
    StandardApplicationSerializer,
    StatusSerializer,
    StatusChangeSerializer,
)
from api.staticdata.statuses.enums import CaseStatusEnum


class ApplicationListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    queryset = StandardApplication.objects.filter(amendment__isnull=True).exclude(submitted_at__isnull=True)
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (PaginatedCSVRenderer,)
    serializer_class = ApplicationSerializer


class StatusListView(viewsets.ViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (CSVRenderer,)

    def list(self, request):
        return Response(StatusSerializer(CaseStatusEnum.all(), many=True).data)


class StatusChangeListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    queryset = Audit.objects.filter(verb=AuditType.UPDATED_STATUS).order_by("created_at")
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (PaginatedCSVRenderer,)
    serializer_class = StatusChangeSerializer


class RFIListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    queryset = EcjuQuery.objects.all()
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (PaginatedCSVRenderer,)
    serializer_class = RFISerializer


class NonWorkingDayListView(viewsets.ViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (CSVRenderer,)

    def get_first_application_created_date(self):
        return StandardApplication.objects.earliest("created_at").created_at.date()

    def get_non_working_days(self, first_date):
        date = first_date
        while date <= datetime.date.today():
            if is_bank_holiday(date):
                yield (date, "BANK_HOLIDAY")
            if is_weekend(date):
                yield (date, "WEEKEND")
            date += datetime.timedelta(days=1)

    def list(self, request):
        first_application_created_date = self.get_first_application_created_date()
        non_working_days = self.get_non_working_days(first_application_created_date)
        return Response(NonWorkingDaySerializer(non_working_days, many=True).data)


class StandardApplicationListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    queryset = StandardApplication.objects.all()
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (CSVRenderer,)
    serializer_class = StandardApplicationSerializer
