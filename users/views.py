from uuid import UUID

import reversion
from django.db.models import Q
from django.http.response import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, generics
from rest_framework.exceptions import ParseError
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from cases.models import Notification
from conf.authentication import (
    ExporterAuthentication,
    ExporterOnlyAuthentication,
    GovAuthentication,
)
from conf.constants import Permissions
from conf.permissions import assert_user_has_permission
from users.libraries.get_user import get_user_by_pk
from users.libraries.user_to_token import user_to_token
from users.models import ExporterUser
from users.serializers import (
    ExporterUserViewSerializer,
    ExporterUserCreateUpdateSerializer,
    NotificationSerializer,
    CaseNotificationGetSerializer,
)


class AuthenticateExporterUser(APIView):
    """
    Authenticate user
    """

    permission_classes = (AllowAny,)

    @swagger_auto_schema(responses={400: "JSON parse error", 403: "Forbidden"})
    def post(self, request, *args, **kwargs):
        """
        Takes user details from sso and checks them against our whitelisted users
        Returns a token which is just our ID for the user
        """
        try:
            data = JSONParser().parse(request)
        except ParseError:
            return JsonResponse(data={"errors": "Invalid Json"}, status=status.HTTP_400_BAD_REQUEST)
        email = data.get("email")

        try:
            user = ExporterUser.objects.get(email=email)
        except ExporterUser.DoesNotExist:
            return JsonResponse(data={"errors": "User not found"}, status=status.HTTP_403_FORBIDDEN)

        token = user_to_token(user)
        return JsonResponse(
            data={
                "token": token,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "lite_api_user_id": str(user.id),
            }
        )


class UserList(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request):
        """
        Returns a list of Exporter users
        """
        serializer = ExporterUserViewSerializer(ExporterUser.objects.all(), many=True)
        return JsonResponse(data={"users": serializer.data})

    @swagger_auto_schema(responses={400: "JSON parse error"})
    def post(self, request):
        """
        Create Exporter within the same organisation that current user is logged into
        """
        data = request.data
        data["organisation"] = request.user.organisation.id
        data["role"] = UUID(data["role"])

        serializer = ExporterUserCreateUpdateSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={"user": serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class UserDetail(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        """
        Get user from pk
        """
        user = get_user_by_pk(pk)
        if request.user.id != pk:
            assert_user_has_permission(user, Permissions.ADMINISTER_USERS, request.user.organisation)

        serializer = ExporterUserViewSerializer(user, context=request.user.organisation)
        return JsonResponse(data={"user": serializer.data})

    @swagger_auto_schema(responses={400: "JSON parse error"})
    def put(self, request, pk):
        """
        Update Exporter user
        """
        user = get_user_by_pk(pk)
        data = JSONParser().parse(request)
        data["organisation"] = request.user.organisation.id

        serializer = ExporterUserCreateUpdateSerializer(user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={"user": serializer.data}, status=status.HTTP_200_OK)

        return JsonResponse(data={"errors": serializer.errors}, status=400)


class UserMeDetail(APIView):
    """
    Get the user from request
    """

    authentication_classes = (ExporterOnlyAuthentication,)

    def get(self, request):
        org_pk = request.headers["Organisation-Id"]
        if org_pk != "None":
            serializer = ExporterUserViewSerializer(request.user, context=org_pk)
        else:
            serializer = ExporterUserViewSerializer(request.user)
        return JsonResponse(data={"user": serializer.data})


class NotificationViewSet(generics.ListAPIView):
    model = Notification
    serializer_class = NotificationSerializer
    authentication_classes = (ExporterAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Notification.objects.all()

    def get_queryset(self):
        organisation_id = self.request.META["HTTP_ORGANISATION_ID"]

        # Get all notifications for the current user and organisation on License Application cases,
        # both those arising from case notes and those arising from ECJU queries
        queryset = Notification.objects.filter(user=self.request.user).filter(
            Q(case_note__case__application__organisation_id=organisation_id)
            | Q(case_note__case__query__organisation_id=organisation_id)
            | Q(query__organisation__id=organisation_id)
            | Q(ecju_query__case__application__organisation_id=organisation_id)
            | Q(ecju_query__case__query__organisation_id=organisation_id)
        )

        if self.request.GET.get("unviewed"):
            queryset = queryset.filter(viewed_at__isnull=True)

        return queryset


class CaseNotification(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request):
        user = request.user
        case = self.request.GET.get("case")

        try:
            notification = Notification.objects.get(user=user, case_activity__case__id=case)
        except Notification.DoesNotExist:
            return JsonResponse(data={"notification": None})

        serializer = CaseNotificationGetSerializer(notification)
        notification.delete()

        return JsonResponse(data={"notification": serializer.data})
