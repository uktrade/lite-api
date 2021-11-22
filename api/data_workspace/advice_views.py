from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination

from api.applications.serializers.advice import Advice
from api.cases.serializers import AdviceSerializer
from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.data_workspace.serializers import AdviceDenialReasonSerializer


class AdviceListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = AdviceSerializer
    pagination_class = LimitOffsetPagination
    queryset = Advice.objects.all()


class AdviceDenialReasonListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = AdviceDenialReasonSerializer
    pagination_class = LimitOffsetPagination
    queryset = Advice.denial_reasons.through.objects.all()
