from django.db.models import Count
from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.settings import api_settings

from rest_framework_csv.renderers import PaginatedCSVRenderer

from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.data_workspace.v2.serializers import LicenceSerializer
from api.licences.enums import LicenceStatus
from api.licences.models import Licence
from api.staticdata.statuses.enums import CaseStatusEnum


class LicencesListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    pagination_class = LimitOffsetPagination
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (PaginatedCSVRenderer,)
    serializer_class = LicenceSerializer

    def get_queryset(self):
        # When an application with all goods as NLR is finalised then the current code
        # creates a licence however the goods on this licence will be empty. This
        # will skew licence data hence exclude them
        return (
            Licence.objects.prefetch_related("goods")
            .annotate(num_licensed_goods=Count("goods"))
            .exclude(status=LicenceStatus.DRAFT)
            .exclude(num_licensed_goods=0)
            .filter(
                case__status__status__in=[
                    CaseStatusEnum.FINALISED,
                    CaseStatusEnum.SUPERSEDED_BY_EXPORTER_EDIT,
                ],
            )
            .order_by("-reference_code")
        )
