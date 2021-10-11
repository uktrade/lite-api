from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination

from api.cases.serializers import SimpleAdviceSerializer, AdviceSerializer
from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.applications.serializers.advice import Advice


class AdviceListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = AdviceSerializer
    pagination_class = LimitOffsetPagination
    queryset = Advice.objects.all()
