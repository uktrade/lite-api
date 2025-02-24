from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.generics import (
    ListAPIView,
    UpdateAPIView,
)

from api.gov_users.caseworker.filters import GovUserFilter
from api.gov_users.caseworker.permissions import (
    CanCaseworkersManageUser,
    CanUserManageQueue,
)
from api.gov_users.caseworker.serializers import (
    GovUserListSerializer,
    GovUserUpdateSerializer,
)

from api.core.authentication import GovAuthentication
from api.users.models import GovUser


class GovUserList(ListAPIView):
    authentication_classes = (GovAuthentication,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = GovUserFilter
    serializer_class = GovUserListSerializer
    queryset = GovUser.objects.order_by("baseuser_ptr__email")


class GovUserUpdate(UpdateAPIView):
    authentication_classes = (GovAuthentication,)
    permission_classes = (CanUserManageQueue | CanCaseworkersManageUser,)
    queryset = GovUser.objects.all()

    serializer_class = GovUserUpdateSerializer
    lookup_field = "pk"
