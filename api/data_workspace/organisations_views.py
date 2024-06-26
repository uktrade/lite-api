from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination

from api.organisations import models, serializers
from api.core.authentication import DataWorkspaceOnlyAuthentication


class OrganisationsView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = serializers.OrganisationListSerializer
    pagination_class = LimitOffsetPagination
    queryset = models.Organisation.objects.all()


class SiteView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = serializers.SiteViewSerializer
    pagination_class = LimitOffsetPagination
    queryset = models.Site.objects.all()
