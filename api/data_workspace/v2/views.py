from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.settings import api_settings

from rest_framework_csv.renderers import PaginatedCSVRenderer

from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.data_workspace.v2.serializers import LicenceSerializer
from api.licences.enums import LicenceStatus
from api.licences.models import Licence


class LicencesListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    pagination_class = LimitOffsetPagination
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (PaginatedCSVRenderer,)
    serializer_class = LicenceSerializer

    def get_queryset(self):
        return Licence.objects.exclude(status=LicenceStatus.DRAFT)
