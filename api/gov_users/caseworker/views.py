from api.gov_users.caseworker.permissions import CanCaseworkersManageUser, CanUserManageQueue
from api.gov_users.caseworker.serializer import GovUserUpdateSerializer, GovUserViewSerializer

from api.core.authentication import GovAuthentication
from api.users.models import GovUser
from rest_framework.generics import ListAPIView, UpdateAPIView


class GovUsersList(ListAPIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = GovUserViewSerializer

    def get_queryset(self):
        queryset = GovUser.objects.all().select_related("role", "team", "baseuser_ptr")
        email = self.request.GET.get("email")
        if email is not None:
            queryset = queryset.filter(baseuser_ptr__email__iexact=email)
        return queryset


class GovUserUpdate(UpdateAPIView):
    authentication_classes = (GovAuthentication,)
    permission_classes = (CanUserManageQueue | CanCaseworkersManageUser,)
    queryset = GovUser.objects.all()

    serializer_class = GovUserUpdateSerializer
    lookup_field = "pk"
