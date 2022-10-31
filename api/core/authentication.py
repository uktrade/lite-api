import logging

from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from django.core.cache import cache
from mohawk import Receiver
from mohawk.exc import HawkFail, AlreadyProcessed
from rest_framework import authentication

from api.core.exceptions import PermissionDeniedError
from api.gov_users.enums import GovUserStatuses
from api.organisations.enums import OrganisationType, OrganisationStatus
from api.organisations.models import Organisation

from api.users.enums import UserStatuses
from api.users.libraries.token_to_user import token_to_user_pk
from api.users.models import UserOrganisationRelationship, ExporterUser, GovUser

GOV_USER_TOKEN_HEADER = "HTTP_GOV_USER_TOKEN"  # nosec

EXPORTER_USER_TOKEN_HEADER = "HTTP_EXPORTER_USER_TOKEN"  # nosec
ORGANISATION_ID = "HTTP_ORGANISATION_ID"

MISSING_TOKEN_ERROR = "You must supply the correct token in your headers"  # nosec
ORGANISATION_DEACTIVATED_ERROR = "Organisation is not activated or not in draft"
USER_DEACTIVATED_ERROR = "User is not active for this organisation"
USER_NOT_FOUND_ERROR = "User does not exist"


logger = logging.getLogger(__name__)


class ExporterBaseAuthentication(authentication.BaseAuthentication):
    def get_header_data(self, request):
        from api.organisations.libraries.get_organisation import get_request_user_organisation_id

        if request.META.get(EXPORTER_USER_TOKEN_HEADER):
            exporter_user_token = request.META.get(EXPORTER_USER_TOKEN_HEADER)
            user_id = token_to_user_pk(exporter_user_token)
            organisation_id = get_request_user_organisation_id(request)
            return exporter_user_token, user_id, organisation_id
        else:
            logger.error("Missing token: %s", EXPORTER_USER_TOKEN_HEADER)
            raise PermissionDeniedError(MISSING_TOKEN_ERROR)

    def get_exporter_user(self, user_id):
        try:
            return ExporterUser.objects.get(pk=user_id)
        except ExporterUser.DoesNotExist:
            raise PermissionDeniedError(USER_NOT_FOUND_ERROR)

    def check_organisation(self, user_id, organisation_id, organisation_status):
        if not Organisation.objects.filter(id=organisation_id, status=organisation_status).exists():
            raise PermissionDeniedError(ORGANISATION_DEACTIVATED_ERROR)

        if not UserOrganisationRelationship.objects.filter(
            user_id=user_id, organisation_id=organisation_id, status=UserStatuses.ACTIVE
        ).exists():
            raise PermissionDeniedError(USER_DEACTIVATED_ERROR)


class ExporterAuthentication(ExporterBaseAuthentication):
    def authenticate(self, request):
        """
        When given an exporter user token and an organisation id, validate that the user belongs to the
        organisation and that they're allowed to access that organisation
        Use this for active organisations
        """
        hawk_receiver = _authenticate(request, _lookup_credentials)

        exporter_user_token, user_id, organisation_id = self.get_header_data(request)

        self.check_organisation(user_id, organisation_id, OrganisationStatus.ACTIVE)

        exporter_user = self.get_exporter_user(user_id)

        return exporter_user.baseuser_ptr, hawk_receiver


class ExporterDraftOrganisationAuthentication(ExporterBaseAuthentication):
    def authenticate(self, request):
        """
        When given an exporter user token and an organisation id, validate that the user belongs to the
        organisation and that they're allowed to access that organisation
        Use this for draft organisations
        """
        hawk_receiver = _authenticate(request, _lookup_credentials)

        exporter_user_token, user_id, organisation_id = self.get_header_data(request)

        self.check_organisation(user_id, organisation_id, OrganisationStatus.DRAFT)

        exporter_user = self.get_exporter_user(user_id)

        return exporter_user.baseuser_ptr, hawk_receiver


class HmrcExporterAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        """
        When given an exporter user token and an HMRC organisation id, validate that the user belongs to the
        organisation and that they're allowed to access that organisation
        """

        from api.organisations.libraries.get_organisation import get_request_user_organisation_id

        hawk_receiver = _authenticate(request, _lookup_credentials)

        if request.META.get(EXPORTER_USER_TOKEN_HEADER):
            exporter_user_token = request.META.get(EXPORTER_USER_TOKEN_HEADER)
            user_id = token_to_user_pk(exporter_user_token)
            organisation_id = get_request_user_organisation_id(request)
        else:
            logger.error("Missing token: %s", EXPORTER_USER_TOKEN_HEADER)
            raise PermissionDeniedError(MISSING_TOKEN_ERROR)

        try:
            exporter_user = ExporterUser.objects.get(pk=user_id)
        except ExporterUser.DoesNotExist:
            raise PermissionDeniedError(USER_NOT_FOUND_ERROR)

        if not Organisation.objects.filter(
            id=organisation_id, status=OrganisationStatus.ACTIVE, type=OrganisationType.HMRC
        ).exists():
            raise PermissionDeniedError(ORGANISATION_DEACTIVATED_ERROR)

        if not UserOrganisationRelationship.objects.filter(
            user_id=user_id, organisation_id=organisation_id, status=UserStatuses.ACTIVE
        ).exists():
            raise PermissionDeniedError(USER_DEACTIVATED_ERROR)

        return exporter_user.baseuser_ptr, hawk_receiver


class ExporterOnlyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        """
        When given an exporter user token, validate that the user exists
        """

        hawk_receiver = _authenticate(request, _lookup_credentials)

        if request.META.get(EXPORTER_USER_TOKEN_HEADER):
            exporter_user_token = request.META.get(EXPORTER_USER_TOKEN_HEADER)
            user_id = token_to_user_pk(exporter_user_token)
        else:
            logger.error("Missing token: %s", EXPORTER_USER_TOKEN_HEADER)
            raise PermissionDeniedError(MISSING_TOKEN_ERROR)

        try:
            exporter_user = ExporterUser.objects.get(pk=user_id)
        except ExporterUser.DoesNotExist:
            raise PermissionDeniedError(USER_NOT_FOUND_ERROR)

        return exporter_user.baseuser_ptr, hawk_receiver


class HawkOnlyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        """
        Establish that the request has come from an authorised LITE API client
        by checking that the request is correctly Hawk signed
        """

        return AnonymousUser(), _authenticate(request, _lookup_credentials)


class HMRCIntegrationOnlyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        """
        Only approve HAWK Signed requests from the HMRC Integration service
        """

        try:
            hawk_receiver = _authenticate(request, _lookup_credentials_hmrc_integration)
        except HawkFail as e:
            logger.exception("Failed HAWK authentication")
            raise e

        return AnonymousUser(), hawk_receiver


class DataWorkspaceOnlyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        """
        Only approve HAWK Signed requests from the Data workspace
        """

        try:
            hawk_receiver = _authenticate(request, _lookup_credentials_data_workspace_access)
        except HawkFail as e:
            logger.exception("Failed HAWK authentication")
            raise e

        return AnonymousUser(), hawk_receiver


class GovAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        """
        When given a gov user token, validate that the user exists and that their account is active
        """

        hawk_receiver = _authenticate(request, _lookup_credentials)

        if request.META.get(GOV_USER_TOKEN_HEADER):
            gov_user_token = request.META.get(GOV_USER_TOKEN_HEADER)
            user_id = token_to_user_pk(gov_user_token)
        else:
            logger.error("Missing token: %s", GOV_USER_TOKEN_HEADER)
            raise PermissionDeniedError(MISSING_TOKEN_ERROR)

        try:
            gov_user = GovUser.objects.get(pk=user_id)
        except GovUser.DoesNotExist:
            raise PermissionDeniedError(USER_NOT_FOUND_ERROR)

        if gov_user.status == GovUserStatuses.DEACTIVATED:
            raise PermissionDeniedError(USER_DEACTIVATED_ERROR)

        return gov_user.baseuser_ptr, hawk_receiver


class SharedAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        """
        When given an exporter or gov user token, validate that the user exists
        """

        exporter_token = request.META.get(EXPORTER_USER_TOKEN_HEADER)

        if exporter_token:
            return ExporterAuthentication().authenticate(request)
        else:
            return GovAuthentication().authenticate(request)


class OrganisationAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        """
        Used to create organisations as a gov or exporter (HMRC or non-registered) user token
        """

        gov_user_token = request.META.get(GOV_USER_TOKEN_HEADER)
        organisation = request.META.get(ORGANISATION_ID, None)

        if gov_user_token:
            return GovAuthentication().authenticate(request)
        elif organisation is not None and organisation != "None":
            return HmrcExporterAuthentication().authenticate(request)
        else:
            return AnonymousUser(), _authenticate(request, _lookup_credentials)


def _authenticate(request, lookup_credentials):
    """
    Raises a HawkFail exception if the passed request cannot be authenticated
    """

    if settings.HAWK_AUTHENTICATION_ENABLED:
        header = request.META.get("HTTP_HAWK_AUTHENTICATION") or request.META.get("HTTP_AUTHORIZATION") or ""
        return Receiver(
            lookup_credentials,
            header,
            request.build_absolute_uri(),
            request.method,
            content=request.body,
            content_type=request.content_type,
            seen_nonce=_seen_nonce,
        )


def _seen_nonce(access_key_id, nonce, _):
    """
    Returns if the passed access_key_id/nonce combination has been
    used within settings.HAWK_RECEIVER_NONCE_EXPIRY_SECONDS
    """

    cache_key = f"hawk:{access_key_id}:{nonce}"

    # cache.add only adds key if it isn't present
    seen_cache_key = not cache.add(cache_key, True, timeout=settings.HAWK_RECEIVER_NONCE_EXPIRY_SECONDS)

    if seen_cache_key:
        raise AlreadyProcessed(f"Already seen nonce {nonce}")

    return seen_cache_key


def _lookup_credentials(access_key_id):
    """
    Raises HawkFail if the access key ID cannot be found.
    """

    try:
        credentials = settings.HAWK_CREDENTIALS[access_key_id]
    except KeyError as exc:
        raise HawkFail(f"No Hawk ID of {access_key_id}") from exc

    return {
        "id": access_key_id,
        "algorithm": "sha256",
        **credentials,
    }


def _lookup_credentials_hmrc_integration(access_key_id):
    """
    Raises HawkFail if the access key ID cannot be found.
    """
    if access_key_id != settings.HAWK_LITE_HMRC_INTEGRATION_CREDENTIALS:
        raise HawkFail(f"No Hawk ID of {access_key_id}")

    return _lookup_credentials(access_key_id)


def _lookup_credentials_data_workspace_access(access_key_id):
    """
    Raises HawkFail if the access key ID is not of Data workspace
    """
    if access_key_id != settings.HAWK_LITE_DATA_WORKSPACE_CREDENTIALS:
        raise HawkFail(f"Incorrect Hawk ID ({access_key_id}) for Data workspace")

    return _lookup_credentials(access_key_id)
