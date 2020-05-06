from django.contrib.auth.models import AnonymousUser
from rest_framework import authentication

from conf.exceptions import PermissionDeniedError
from gov_users.enums import GovUserStatuses
from organisations.enums import OrganisationType, OrganisationStatus
from organisations.models import Organisation
from users.enums import UserStatuses
from users.libraries.get_user import get_user_by_pk, get_user_organisations
from users.libraries.token_to_user import token_to_user_pk
from users.models import UserOrganisationRelationship, ExporterUser, GovUser

GOV_USER_TOKEN_HEADER = "HTTP_GOV_USER_TOKEN"  # nosec

EXPORTER_USER_TOKEN_HEADER = "HTTP_EXPORTER_USER_TOKEN"  # nosec
ORGANISATION_ID = "HTTP_ORGANISATION_ID"

MISSING_TOKEN_ERROR = "You must supply the correct token in your headers"
ORGANISATION_DEACTIVATED_ERROR = "Organisation is not activated"
USER_DEACTIVATED_ERROR = "User is not active for this organisation"
USER_NOT_FOUND_ERROR = "User does not exist"


class ExporterAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        """
        When given a user token and an organisation id, validate that the user belongs to the
        organisation and that they're allowed to access that organisation
        """
        if request.META.get(EXPORTER_USER_TOKEN_HEADER):
            exporter_user_token = request.META.get(EXPORTER_USER_TOKEN_HEADER)
            user_id = token_to_user_pk(exporter_user_token)
            organisation_id = request.META.get(ORGANISATION_ID)
        else:
            raise PermissionDeniedError(MISSING_TOKEN_ERROR)

        if not Organisation.objects.filter(id=organisation_id, status=OrganisationStatus.ACTIVE).exists():
            raise PermissionDeniedError(ORGANISATION_DEACTIVATED_ERROR)

        if not UserOrganisationRelationship.objects.filter(
            user_id=user_id, organisation_id=organisation_id, status=UserStatuses.ACTIVE
        ).exists():
            raise PermissionDeniedError(USER_DEACTIVATED_ERROR)

        try:
            user = ExporterUser.objects.get(id=user_id)
        except ExporterUser.DoesNotExist:
            raise PermissionDeniedError(USER_NOT_FOUND_ERROR)

        return user, None


class HmrcExporterAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        """
        When given a user token and an organisation id, validate that the user belongs to the
        organisation and that they're allowed to access that organisation
        """
        if request.META.get(EXPORTER_USER_TOKEN_HEADER):
            exporter_user_token = request.META.get(EXPORTER_USER_TOKEN_HEADER)
            user_id = token_to_user_pk(exporter_user_token)
            organisation_id = request.META.get(ORGANISATION_ID)
        else:
            raise PermissionDeniedError(MISSING_TOKEN_ERROR)

        if not Organisation.objects.filter(
            id=organisation_id, status=OrganisationStatus.ACTIVE, type=OrganisationType.HMRC
        ).exists():
            raise PermissionDeniedError(ORGANISATION_DEACTIVATED_ERROR)

        if not UserOrganisationRelationship.objects.filter(
            user_id=user_id, organisation_id=organisation_id, status=UserStatuses.ACTIVE
        ).exists():
            raise PermissionDeniedError(USER_DEACTIVATED_ERROR)

        try:
            user = ExporterUser.objects.get(id=user_id)
        except ExporterUser.DoesNotExist:
            raise PermissionDeniedError(USER_NOT_FOUND_ERROR)

        return user, None


class GovAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        """
        When given a user token token validate that they're a government user
        and that their account is active
        """
        if request.META.get(GOV_USER_TOKEN_HEADER):
            gov_user_token = request.META.get(GOV_USER_TOKEN_HEADER)
            user_id = token_to_user_pk(gov_user_token)
        else:
            raise PermissionDeniedError(MISSING_TOKEN_ERROR)

        gov_user = GovUser.objects.filter(id=user_id, status=GovUserStatuses.ACTIVE)

        if not gov_user.exists():
            raise PermissionDeniedError(USER_DEACTIVATED_ERROR)

        return gov_user.first(), None


class SharedAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        exporter_token = request.META.get(EXPORTER_USER_TOKEN_HEADER)

        if exporter_token:
            exporter_auth = ExporterAuthentication()
            return exporter_auth.authenticate(request)
        else:
            gov_auth = GovAuthentication()
            return gov_auth.authenticate(request)


class OrganisationAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        gov_user_token = request.META.get(GOV_USER_TOKEN_HEADER)
        organisation = request.META.get(ORGANISATION_ID, None)

        if gov_user_token:
            return GovAuthentication().authenticate(request)
        elif organisation is not None and organisation != "None":
            return HmrcExporterAuthentication().authenticate(request)
        else:
            return AnonymousUser, None
