import operator
from functools import reduce

from django.db.models import Q, F, ExpressionWrapper, BooleanField
from django.http import JsonResponse
from rest_framework import status, generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from api.core.authentication import SharedAuthentication
from api.core.constants import Roles, ExporterPermissions
from api.core.permissions import assert_user_has_permission
from api.gov_users.serializers import RoleListSerializer
from lite_content.lite_api import strings
from api.organisations.enums import OrganisationType
from api.organisations.libraries.get_organisation import get_organisation_by_pk
from api.organisations.models import Site
from api.organisations.serializers import (
    OrganisationUserListSerializer,
    CommercialOrganisationUserListSerializer,
    SiteListSerializer,
)
from api.users.enums import UserStatuses
from api.users.libraries.get_user import get_user_by_pk, get_user_organisation_relationship
from api.users.models import ExporterUser, Role
from api.users.serializers import (
    ExporterUserCreateUpdateSerializer,
    UserOrganisationRelationshipSerializer,
)
from api.users.services import filter_roles_by_user_role


class UsersList(generics.ListCreateAPIView):
    authentication_classes = (SharedAuthentication,)

    def get_serializer_class(self):
        organisation = get_organisation_by_pk(self.kwargs["org_pk"])
        if organisation.type == OrganisationType.INDIVIDUAL and hasattr(self.request.user, "govuser"):
            return OrganisationUserListSerializer
        else:
            return CommercialOrganisationUserListSerializer

    def get_queryset(self):
        _status = self.request.GET.get("status")
        exclude_permission = self.request.GET.get("exclude_permission")
        organisation_id = self.kwargs["org_pk"]
        organisation = get_organisation_by_pk(self.kwargs["org_pk"])

        if hasattr(self.request.user, "exporteruser"):
            assert_user_has_permission(
                self.request.user.exporteruser, ExporterPermissions.ADMINISTER_USERS, organisation_id
            )

        query = [Q(relationship__organisation__id=organisation_id)]

        if _status:
            query.append(Q(relationship__status=UserStatuses.from_string(_status)))

        values = ("baseuser_ptr_id", "first_name", "last_name", "email", "status", "role_name", "pending")
        if (
            organisation.type == OrganisationType.COMMERCIAL
            or organisation.type == OrganisationType.HMRC
            or hasattr(self.request.user, "exporteruser")
        ):
            values += ("phone_number",)

        return (
            ExporterUser.objects.filter(reduce(operator.and_, query))
            .exclude(relationship__role__permissions__in=[exclude_permission])
            .select_related("relationship__role")
            .annotate(
                first_name=F("baseuser_ptr__first_name"),
                last_name=F("baseuser_ptr__last_name"),
                email=F("baseuser_ptr__email"),
                status=F("relationship__status"),
                role_name=F("relationship__role__name"),
                phone_number=F("baseuser_ptr__phone_number"),
                pending=ExpressionWrapper(Q(baseuser_ptr__first_name=""), output_field=BooleanField()),
            )
            .values(*values)
        )

    def post(self, request, org_pk):
        """
        Create an exporter user within the specified organisation
        """
        if hasattr(request.user, "exporteruser"):
            assert_user_has_permission(request.user.exporteruser, ExporterPermissions.ADMINISTER_USERS, org_pk)
        data = JSONParser().parse(request)
        data["organisation"] = str(org_pk)
        serializer = ExporterUserCreateUpdateSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={"user": serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class UserDetail(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request, org_pk, user_pk):
        """
        Return a user from the specified organisation
        """
        is_self = str(request.user.pk) == str(user_pk)
        if not is_self and hasattr(request.user, "exporteruser"):
            assert_user_has_permission(request.user.exporteruser, ExporterPermissions.ADMINISTER_USERS, org_pk)

        relationship = get_user_organisation_relationship(user_pk, org_pk)
        sites = Site.objects.get_by_user_organisation_relationship(relationship)

        return JsonResponse(
            data={
                "id": relationship.user.pk,
                "first_name": relationship.user.first_name,
                "last_name": relationship.user.last_name,
                "email": relationship.user.email,
                "status": relationship.status,
                "role": RoleListSerializer(relationship.role).data,
                "sites": SiteListSerializer(sites, many=True).data,
            }
        )

    def put(self, request, org_pk, user_pk):
        """
        Update the status of a user
        """
        if hasattr(request.user, "exporteruser"):
            assert_user_has_permission(request.user.exporteruser, ExporterPermissions.ADMINISTER_USERS, org_pk)

        data = JSONParser().parse(request)
        user = get_user_by_pk(user_pk)
        org = get_organisation_by_pk(org_pk)

        # Set the user's status in that org
        user_relationship = org.get_user_relationship(user)
        user.status = user_relationship.status

        # Cannot perform actions on another super user without super user role
        if (
            data.get("role") == Roles.EXPORTER_ADMINISTRATOR_ROLE_ID
            or user.get_role(org_pk).id == Roles.EXPORTER_ADMINISTRATOR_ROLE_ID
        ) and not request.user.exporteruser.get_role(org_pk).id == Roles.EXPORTER_ADMINISTRATOR_ROLE_ID:
            raise PermissionDenied()

        # Don't allow a user to update their own status or that of a super user
        if "status" in data.keys():
            if user.pk == request.user.pk:
                return JsonResponse(
                    data={"errors": "A user cannot change their own status"}, status=status.HTTP_400_BAD_REQUEST
                )
            elif user.get_role(org_pk).id == Roles.EXPORTER_ADMINISTRATOR_ROLE_ID and data["status"] == "Deactivated":
                raise PermissionDenied()

        # Cannot remove super user from yourself
        if "role" in data.keys():
            if user.pk == request.user.pk:
                return JsonResponse(
                    data={"errors": strings.Users.ORGANISATIONS_VIEWS_USER_CANNOT_CHANGE_OWN_ROLE},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif (
                user.pk == request.user.pk and request.user.get_role(org_pk).id == Roles.EXPORTER_ADMINISTRATOR_ROLE_ID
            ):
                return JsonResponse(
                    data={"errors": "A user cannot remove super user from themselves"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # Cannot assign a role, you do not have access to
            exporter_roles = [str(role) for role in Roles.EXPORTER_PRESET_ROLES]
            user_roles = [
                str(role.id)
                for role in filter_roles_by_user_role(request.user, Role.objects.filter(organisation=org_pk), org_pk)
            ]

            if data["role"] not in exporter_roles + user_roles:
                raise PermissionDenied()

        serializer = UserOrganisationRelationshipSerializer(instance=user_relationship, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={"user_relationship": serializer.data})

        return JsonResponse(data={"errors": serializer.errors})
