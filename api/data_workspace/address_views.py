from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination

from api.addresses.models import Address
from api.addresses.serializers import AddressSerializer
from api.core.authentication import DataWorkspaceOnlyAuthentication


class AddressView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = AddressSerializer
    pagination_class = LimitOffsetPagination
    queryset = Address.objects.all()
