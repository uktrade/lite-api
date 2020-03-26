from uuid import UUID

from django.db.models import Count, CharField, Value, QuerySet
from django.http.response import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, serializers
from rest_framework.exceptions import ParseError, PermissionDenied
from rest_framework.generics import UpdateAPIView, ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from cases.enums import CaseTypeTypeEnum, CaseTypeSubTypeEnum
from conf.authentication import ExporterAuthentication, ExporterOnlyAuthentication, GovAuthentication
from conf.constants import ExporterPermissions
from conf.exceptions import NotFoundError
from conf.helpers import convert_queryset_to_str, get_value_from_enum, date_to_drf_date
from conf.permissions import assert_user_has_permission
from lite_content.lite_api.strings import Users
from organisations.enums import OrganisationStatus
from organisations.libraries.get_organisation import get_organisation_by_pk
from organisations.libraries.get_site import get_site
from organisations.models import Site
from queues.models import Queue
from users.libraries.get_user import (
    get_user_by_pk,
    get_user_organisation_relationship,
)
from users.libraries.user_to_token import user_to_token
from users.models import ExporterUser, ExporterNotification, GovUser, UserOrganisationRelationship
from users.serializers import (
    ExporterUserViewSerializer,
    ExporterUserCreateUpdateSerializer,
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
        relationship = get_user_organisation_relationship(user, request.user.organisation)

        serializer = ExporterUserViewSerializer(user, context=relationship)
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
        user = request.user
        relationships = UserOrganisationRelationship.objects.filter(user=user).select_related("organisation")

        # Returning a dict over a serializer for performance reasons
        # This endpoint is called often, so it needs to be as fast as possible
        data = {
            "id": request.user.id,
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "organisations": [
                {
                    "id": relationship.organisation.id,
                    "name": relationship.organisation.name,
                    "joined_at": date_to_drf_date(relationship.created_at),
                    "status": {
                        "key": relationship.organisation.status,
                        "value": get_value_from_enum(relationship.organisation.status, OrganisationStatus),
                    },
                }
                for relationship in relationships
            ],
        }

        if org_pk != "None":
            relationship = get_user_organisation_relationship(user, org_pk)
            data.update(
                {
                    "role": {
                        "id": relationship.role.id,
                        "permissions": convert_queryset_to_str(
                            relationship.role.permissions.values_list("id", flat=True)
                        ),
                    }
                }
            )

        return JsonResponse(data=data)


class NotificationViewSet(APIView):
    authentication_classes = (ExporterAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = ExporterNotification.objects.all()

    def get(self, request):
        """
        Count the number of application, eua_query and goods_query exporter user notifications
        """
        notification_queryset = self.queryset.filter(user=request.user, organisation=request.user.organisation)
        application_queryset = self._build_queryset(
            queryset=notification_queryset,
            filter=dict(case__case_type__type=CaseTypeTypeEnum.APPLICATION),
            type=CaseTypeTypeEnum.APPLICATION,
        )
        eua_query_queryset = self._build_queryset(
            queryset=notification_queryset,
            filter=dict(case__case_type__sub_type=CaseTypeSubTypeEnum.EUA),
            type=CaseTypeSubTypeEnum.EUA,
        )
        goods_query_queryset = self._build_queryset(
            queryset=notification_queryset,
            filter=dict(case__case_type__sub_type=CaseTypeSubTypeEnum.GOODS),
            type=CaseTypeSubTypeEnum.GOODS,
        )
        notification_queryset = application_queryset.union(eua_query_queryset).union(goods_query_queryset)

        data = {"notifications": {row["type"]: row["count"] for row in notification_queryset}}
        return JsonResponse(data=data, status=status.HTTP_200_OK)

    @staticmethod
    def _build_queryset(queryset: QuerySet, filter: dict, type: str) -> QuerySet:
        """
        :param queryset: An ExporterNotification QuerySet
        :param filter: Additional filter containing 1 key-value pair
        :param type: An annotated static field in the queryset
        :return: An ExporterNotification QuerySet containing only the type and count of rows found matching the filter
        """
        return (
            queryset.filter(**filter)
            .values(list(filter)[0])
            .annotate(type=Value(type, CharField()), count=Count("case"))
            .values("type", "count")
        )


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
            raise serializers.ValidationError({"sites": [Users.SELECT_AT_LEAST_ONE_SITE_ERROR]})

        # Ensure user has access to the sites they're trying to assign the user to
        for site in sites:
            site = get_site(site, organisation)
            if site not in request_user_sites:
                raise NotFoundError("You don't have access to the sites you're trying to assign the user to.")

        user_organisation_relationship.sites.set(combined_sites)

        return JsonResponse(data={"status": "success"})


class UserTeamQueues(ListAPIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        gov_user_team = GovUser.objects.filter(id=pk).values("team_id")
        queues = Queue.objects.filter(team_id__in=gov_user_team).values_list("id", "name")
        return JsonResponse(data={"queues": list(queues)}, status=status.HTTP_200_OK)
