from functools import reduce
from operator import or_
from uuid import UUID

from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Q
from django.http.response import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, serializers
from rest_framework.exceptions import ParseError, PermissionDenied
from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from audit_trail.models import Audit
from conf.authentication import ExporterAuthentication, ExporterOnlyAuthentication, GovAuthentication
from conf.constants import ExporterPermissions
from conf.exceptions import NotFoundError
from conf.helpers import str_to_bool
from conf.permissions import assert_user_has_permission
from organisations.libraries.get_organisation import get_organisation_by_pk
from organisations.libraries.get_site import get_site
from organisations.models import Site
from users.libraries.get_user import get_user_by_pk, get_user_organisation_relationship
from users.libraries.user_to_token import user_to_token
from users.models import ExporterUser, ExporterNotification, GovNotification
from users.serializers import (
    ExporterUserViewSerializer,
    ExporterUserCreateUpdateSerializer,
    ExporterNotificationSerializer,
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
            data = request.data
        except ParseError:
            return JsonResponse(data={"errors": "Invalid Json"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = ExporterUser.objects.get(email=data.get("email"))

            # Update the user's first and last names
            user.first_name = data.get("user_profile").get("first_name")
            user.last_name = data.get("user_profile").get("last_name")
            user.save()
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
            assert_user_has_permission(request.user, ExporterPermissions.ADMINISTER_USERS, request.user.organisation)

        serializer = ExporterUserViewSerializer(user, context=request.user.organisation)
        return JsonResponse(data={"user": serializer.data})

    @swagger_auto_schema(responses={400: "JSON parse error"})
    def put(self, request, pk):
        """
        Update Exporter user
        """
        user = get_user_by_pk(pk)
        data = request.data
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


class NotificationViewSet(APIView):
    authentication_classes = (ExporterAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = ExporterNotification.objects.all()
    serializer_class = ExporterNotificationSerializer

    def get(self, request):
        data = {}
        queryset = ExporterNotification.objects.filter(user=request.user, organisation=request.user.organisation)

        # Iterate through the case types and build an 'OR' queryset
        # to get notifications matching different case types
        case_types = request.GET.getlist("case_type")
        if case_types:
            queries = [Q(case__type=case_type) for case_type in case_types]
            # Collapses the queries list into a usable filter
            queryset = queryset.filter(reduce(or_, queries))

        # Count the number of notifications for each type
        count_queryset = queryset.values("case__type").annotate(total=Count("case__type"))
        data["notification_count"] = {
            content_type["case__type"]: content_type["total"] for content_type in count_queryset
        }

        # Serialize notifications
        if not str_to_bool(request.GET.get("count_only")):
            data["notifications"] = ExporterNotificationSerializer(queryset, many=True).data

        return JsonResponse(data=data, status=status.HTTP_200_OK)


class CaseNotification(APIView):
    authentication_classes = (GovAuthentication,)
    queryset = GovNotification.objects.all()

    def get(self, request):
        user = request.user
        case = self.request.GET.get("case")
        notification_data = None

        content_type = ContentType.objects.get_for_model(Audit)
        queryset = GovNotification.objects.filter(user=user, content_type=content_type, case__id=case)

        if queryset.exists():
            notification = queryset.first()
            notification_data = CaseNotificationGetSerializer(notification).data
            notification.delete()

        return JsonResponse(data={"notification": notification_data}, status=status.HTTP_200_OK)


class AssignSites(UpdateAPIView):
    authentication_classes = (ExporterAuthentication,)

    def put(self, request, *args, **kwargs):
        # Ensure that the request user isn't the same as the user being acted upon
        if str(request.user.id) == str(kwargs["pk"]):
            raise PermissionDenied()

        sites = request.data.get("sites", [])
        organisation = get_organisation_by_pk(self.request.META["HTTP_ORGANISATION_ID"])
        request_user_relationship = get_user_organisation_relationship(request.user, organisation)
        user_organisation_relationship = get_user_organisation_relationship(kwargs["pk"], organisation)

        # Get a list of all the sites that the request user has access to!
        request_user_sites = list(Site.objects.get_by_user_organisation_relationship(request_user_relationship))
        user_sites = list(Site.objects.get_by_user_organisation_relationship(user_organisation_relationship))
        diff_sites = [x for x in user_sites if x not in request_user_sites]
        combined_sites = diff_sites + sites

        # If (after the PUT) the user isn't assigned to any sites, raise an error
        if not combined_sites:
            raise serializers.ValidationError({"errors": {"sites": ["Select at least one site to assign the user to"]}})

        # Ensure user has access to the sites they're trying to assign the user to
        for site in sites:
            site = get_site(site, organisation)
            if site not in request_user_sites:
                raise NotFoundError("You don't have access to the sites you're trying to assign the user to.")

        user_organisation_relationship.sites.set(combined_sites)

        return JsonResponse(data={"status": "success"})
