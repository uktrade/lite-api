from uuid import UUID

from django.http.response import JsonResponse
from rest_framework import status, serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import UpdateAPIView, ListAPIView
from rest_framework.views import APIView

from api.cases.enums import CaseTypeTypeEnum, CaseTypeSubTypeEnum
from api.core.authentication import (
    ExporterAuthentication,
    GovAuthentication,
    ExporterOnlyAuthentication,
    HawkOnlyAuthentication,
)
from api.core.constants import ExporterPermissions
from api.core.exceptions import NotFoundError
from api.core.helpers import (
    convert_queryset_to_str,
    get_exporter_frontend_url,
    get_value_from_enum,
    date_to_drf_date,
    str_to_bool,
)
from api.core.permissions import assert_user_has_permission, check_user_has_permission
from lite_content.lite_api import strings
from lite_content.lite_api.strings import Users
from api.organisations.enums import OrganisationStatus
from api.organisations.libraries.get_organisation import get_request_user_organisation_id, get_request_user_organisation
from api.organisations.libraries.get_site import get_site
from api.organisations.models import Site
from api.queues.models import Queue
from api.users import notify
from api.users.libraries.get_user import (
    get_user_by_pk,
    get_user_organisation_relationship,
)
from api.users.libraries.user_to_token import user_to_token
from api.users.models import ExporterUser, ExporterNotification, GovUser, UserOrganisationRelationship
from api.users.serializers import (
    ExporterUserViewSerializer,
    ExporterUserCreateUpdateSerializer,
)


class AuthenticateExporterUser(APIView):
    """
    Authenticate user
    """

    authentication_classes = (HawkOnlyAuthentication,)

    def post(self, request, *args, **kwargs):
        """
        Takes user details from sso and checks them against our whitelisted users
        Returns a token which is just our ID for the user
        """

        data = request.data
        first_name = data.get("user_profile", {}).get("first_name", "")
        last_name = data.get("user_profile", {}).get("last_name", "")
        external_id = data.get("sub", "")
        if not data.get("email"):
            return JsonResponse(
                data={"errors": ["No email provided"]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            user = ExporterUser.objects.get(baseuser_ptr__email__iexact=data.get("email"))

            # Update the user's first and last names
            user.baseuser_ptr.first_name = first_name
            user.baseuser_ptr.last_name = last_name
            user.baseuser_ptr.pending = False
            user.baseuser_ptr.save()

            if not user.external_id and external_id:
                # This is saving external_id from external SSO service only needs to be done once.
                # If we have a sub we have an open_id from an external system
                user.external_id = external_id
                user.save()

        except ExporterUser.DoesNotExist:
            return JsonResponse(
                data={"errors": [strings.Login.Error.USER_NOT_FOUND]}, status=status.HTTP_401_UNAUTHORIZED
            )

        token = user_to_token(user.baseuser_ptr)
        return JsonResponse(
            data={
                "token": token,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "lite_api_user_id": str(user.pk),
            }
        )


class CreateUser(APIView):
    authentication_classes = (ExporterAuthentication,)

    def post(self, request):
        """
        Create Exporter within the same organisation that current user is logged into
        """
        data = request.data
        organisation = get_request_user_organisation(request)
        data["organisation"] = organisation.pk
        data["role"] = UUID(data["role"])

        serializer = ExporterUserCreateUpdateSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            notify.notify_exporter_user_added(
                serializer.validated_data["email"],
                {"organisation_name": organisation.name, "exporter_frontend_url": get_exporter_frontend_url("/")},
            )
            return JsonResponse(data={"user": serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class UserDetail(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        """
        Get user from pk
        """
        user = get_user_by_pk(pk)
        organisation = get_request_user_organisation(request)
        if request.user.pk != pk:
            assert_user_has_permission(request.user.exporteruser, ExporterPermissions.ADMINISTER_USERS, organisation)
        relationship = get_user_organisation_relationship(user, organisation)

        serializer = ExporterUserViewSerializer(user, context=relationship)
        return JsonResponse(data={"user": serializer.data})

    def put(self, request, pk):
        """
        Update Exporter user
        """
        user = get_user_by_pk(pk)
        data = request.data
        data["organisation"] = get_request_user_organisation_id(request)

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
        org_pk = request.headers["ORGANISATION-ID"]
        user = request.user.exporteruser
        relationships = UserOrganisationRelationship.objects.select_related("organisation").filter(user=user)

        if str_to_bool(request.GET.get("in_review", False)):
            relationships = relationships.filter(organisation__status=OrganisationStatus.IN_REVIEW)
        elif str_to_bool(request.GET.get("draft", False)):
            relationships = relationships.filter(organisation__status=OrganisationStatus.DRAFT)
        else:
            relationships = relationships.exclude(
                organisation__status__in=[OrganisationStatus.IN_REVIEW, OrganisationStatus.REJECTED]
            )

        # Returning a dict over a serializer for performance reasons
        # This endpoint is called often, so it needs to be as fast as possible
        data = {
            "id": user.pk,
            "first_name": user.first_name,
            "last_name": user.last_name,
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
                        "id": relationship.role_id,
                        "permissions": convert_queryset_to_str(
                            relationship.role.permissions.values_list("id", flat=True)
                        ),
                    }
                }
            )

        return JsonResponse(data=data)


class NotificationViewSet(APIView):
    authentication_classes = (ExporterAuthentication,)
    queryset = ExporterNotification.objects.all()

    def get(self, request):
        """
        Count the number of application, eua_query and goods_query exporter user notifications
        """
        organisation = get_request_user_organisation(request)
        notifications_list = list(
            self.queryset.filter(user_id=request.user.pk, organisation_id=organisation.id)
            .prefetch_related("case__case_type", "case__compliancesitecase")
            .values(
                "case__case_type__sub_type",
                "case__case_type__type",
                "case__compliancesitecase__site_id",
                "case__compliancevisitcase__site_case__site_id",
            )
        )
        case_types = [notification["case__case_type__type"] for notification in notifications_list]
        case_sub_types = [notification["case__case_type__sub_type"] for notification in notifications_list]
        notifications = {
            CaseTypeTypeEnum.APPLICATION: case_types.count(CaseTypeTypeEnum.APPLICATION),
            CaseTypeSubTypeEnum.EUA: case_sub_types.count(CaseTypeSubTypeEnum.EUA),
            CaseTypeSubTypeEnum.GOODS: case_sub_types.count(CaseTypeSubTypeEnum.GOODS),
        }

        # Compliance
        can_administer_sites = check_user_has_permission(
            self.request.user.exporteruser, ExporterPermissions.ADMINISTER_SITES, organisation
        )

        request_user_sites = (
            list(
                Site.objects.get_by_user_and_organisation(request.user.exporteruser, organisation).values_list(
                    "id", flat=True
                )
            )
            if not can_administer_sites
            else []
        )

        notifications[CaseTypeTypeEnum.COMPLIANCE] = len(
            [
                notification
                for notification in notifications_list
                if (notification["case__compliancesitecase__site_id"] and can_administer_sites)
                or (notification["case__compliancevisitcase__site_case__site_id"] and can_administer_sites)
                or notification["case__compliancesitecase__site_id"] in request_user_sites
                or notification["case__compliancevisitcase__site_case__site_id"] in request_user_sites
            ]
        )

        return JsonResponse(data={"notifications": notifications}, status=status.HTTP_200_OK)


class AssignSites(UpdateAPIView):
    authentication_classes = (ExporterAuthentication,)

    def put(self, request, *args, **kwargs):
        # Ensure that the request user isn't the same as the user being acted upon
        if str(request.user.pk) == str(kwargs["pk"]):
            raise PermissionDenied()

        sites = request.data.get("sites", [])
        organisation = get_request_user_organisation(request)
        request_user_relationship = get_user_organisation_relationship(request.user.exporteruser, organisation)
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
        gov_user_team = GovUser.objects.filter(pk=pk).values("team_id")
        queues = Queue.objects.filter(team_id__in=gov_user_team).values_list("id", "name")
        return JsonResponse(data={"queues": list(queues)}, status=status.HTTP_200_OK)
