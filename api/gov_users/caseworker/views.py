from django.http import JsonResponse
from rest_framework import status
from api.gov_users.enums import GovUserStatuses

from api.core.authentication import GovAuthentication
from api.gov_users.serializers import GovUserCreateOrUpdateSerializer
from api.users.models import GovUser
from api.users.serializers import GovUserViewSerializer
from rest_framework.generics import ListAPIView, UpdateAPIView
from .permissions import CanCaseworkersManageUser


class GovUsersList(ListAPIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = GovUserViewSerializer

    def get_queryset(self):
        queryset = GovUser.objects.all()
        email = self.request.GET.get("email")
        if email is not None:
            queryset = queryset.filter(baseuser_ptr__email=email)
        return queryset


class GovUserUpdate(UpdateAPIView):
    authentication_classes = (GovAuthentication,)
    permission_classes = [
        CanCaseworkersManageUser,
    ]

    queryset = GovUser.objects.all()

    serializer_class = GovUserCreateOrUpdateSerializer
    lookup_field = "pk"

    def update(self, request, pk):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True, is_creating=False)
        if serializer.is_valid():
            # Remove user from assigned cases
            if request.data.get("status") == GovUserStatuses.DEACTIVATED:
                instance.unassign_from_cases()
            serializer.save()
            return JsonResponse(data={"gov_user": serializer.data}, status=status.HTTP_200_OK)

        else:
            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
