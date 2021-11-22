from django.db.models import Q
from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination

from api.cases.enums import CaseTypeEnum
from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.open_general_licences.models import OpenGeneralLicence
from api.open_general_licences.serializers import OpenGeneralLicenceSerializer
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
        # OGL's are always hidden as we don't treat them as a licence
        # and they shouldn't be viewed from this endpoint
        models.Licence.objects.exclude(
            Q(case__status__in=non_active_states)
            | Q(case__case_type__id__in=CaseTypeEnum.OPEN_GENERAL_LICENCE_IDS)
            | Q(status=enums.LicenceStatus.DRAFT)
        )
        .order_by("created_at")
        .reverse()
    )


class OpenGeneralLicenceListDW(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = OpenGeneralLicenceSerializer
    pagination_class = LimitOffsetPagination
    queryset = (
        OpenGeneralLicence.objects.all()
        .select_related("case_type")
        .prefetch_related("countries", "control_list_entries")
    )


class GoodOnLicenceList(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = serializers.GoodOnLicenceReportsViewSerializer
    pagination_class = LimitOffsetPagination
    queryset = models.GoodOnLicence.objects.all()


class LicencesList(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = serializers.LicenceListSerializer
    pagination_class = LimitOffsetPagination
    queryset = models.Licence.objects.all()
