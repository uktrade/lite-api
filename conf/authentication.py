import logging

from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from mohawk import Receiver
from mohawk.exc import HawkFail, AlreadyProcessed
from rest_framework import authentication

from conf import settings
from conf.exceptions import PermissionDeniedError
from conf.settings import HAWK_AUTHENTICATION_ENABLED
from gov_users.enums import GovUserStatuses
from organisations.enums import OrganisationType, OrganisationStatus
from organisations.models import Organisation
from users.enums import UserStatuses
from users.libraries.token_to_user import token_to_user_pk
from users.models import UserOrganisationRelationship, ExporterUser, GovUser

GOV_USER_TOKEN_HEADER = "HTTP_GOV_USER_TOKEN"  # nosec

EXPORTER_USER_TOKEN_HEADER = "HTTP_EXPORTER_USER_TOKEN"  # nosec
ORGANISATION_ID = "HTTP_ORGANISATION_ID"

MISSING_TOKEN_ERROR = "You must supply the correct token in your headers"  # nosec
ORGANISATION_DEACTIVATED_ERROR = "Organisation is not activated"
USER_DEACTIVATED_ERROR = "User is not active for this organisation"
USER_NOT_FOUND_ERROR = "User does not exist"


class ExporterAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        """
        When given an exporter user token and an organisation id, validate that the user belongs to the
        organisation and that they're allowed to access that organisation
        """

        from organisations.libraries.get_organisation import get_request_user_organisation_id

        _, hawk_receiver = HawkOnlyAuthentication().authenticate(request)

        if request.META.get(EXPORTER_USER_TOKEN_HEADER):
            exporter_user_token = request.META.get(EXPORTER_USER_TOKEN_HEADER)
            user_id = token_to_user_pk(exporter_user_token)
            organisation_id = get_request_user_organisation_id(request)
        else:
            raise PermissionDeniedError(MISSING_TOKEN_ERROR)

        if not Organisation.objects.filter(id=organisation_id, status=OrganisationStatus.ACTIVE).exists():
            raise PermissionDeniedError(ORGANISATION_DEACTIVATED_ERROR)

        if not UserOrganisationRelationship.objects.filter(
            user_id=user_id, organisation_id=organisation_id, status=UserStatuses.ACTIVE
        ).exists():
            raise PermissionDeniedError(USER_DEACTIVATED_ERROR)

        try:
            exporter_user = ExporterUser.objects.get(id=user_id)
        except ExporterUser.DoesNotExist:
            raise PermissionDeniedError(USER_NOT_FOUND_ERROR)

        return exporter_user, hawk_receiver


class HmrcExporterAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        """
        When given an exporter user token and an HMRC organisation id, validate that the user belongs to the
        organisation and that they're allowed to access that organisation
        """
        from organisations.libraries.get_organisation import get_request_user_organisation_id

        _, hawk_receiver = HawkOnlyAuthentication().authenticate(request)

        if request.META.get(EXPORTER_USER_TOKEN_HEADER):
            exporter_user_token = request.META.get(EXPORTER_USER_TOKEN_HEADER)
            user_id = token_to_user_pk(exporter_user_token)
            organisation_id = get_request_user_organisation_id(request)
        else:
            raise PermissionDeniedError(MISSING_TOKEN_ERROR)

        try:
            exporter_user = ExporterUser.objects.get(id=user_id)
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

        return exporter_user, hawk_receiver


class ExporterOnlyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        """
        When given an exporter user token, validate that the user exists
        """

        _, hawk_receiver = HawkOnlyAuthentication().authenticate(request)

        if request.META.get(EXPORTER_USER_TOKEN_HEADER):
            exporter_user_token = request.META.get(EXPORTER_USER_TOKEN_HEADER)
            user_id = token_to_user_pk(exporter_user_token)
        else:
            raise PermissionDeniedError(MISSING_TOKEN_ERROR)

        try:
            exporter_user = ExporterUser.objects.get(id=user_id)
        except ExporterUser.DoesNotExist:
            raise PermissionDeniedError(USER_NOT_FOUND_ERROR)

        return exporter_user, hawk_receiver


class HawkOnlyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        """
        Establish that the request has come from an authorised LITE API client
        by checking that the request is correctly Hawk signed
        """

        try:
            hawk_receiver = _authenticate(request)
        except HawkFail as e:
            logging.warning(f"Failed HAWK authentication {e}")
            raise e

        return AnonymousUser, hawk_receiver


class GovAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        """
        When given an exporter user token, validate that the user exists and that their account is active
        """

        _, hawk_receiver = HawkOnlyAuthentication().authenticate(request)

        if request.META.get(GOV_USER_TOKEN_HEADER):
            gov_user_token = request.META.get(GOV_USER_TOKEN_HEADER)
            user_id = token_to_user_pk(gov_user_token)
        else:
            raise PermissionDeniedError(MISSING_TOKEN_ERROR)

        try:
            gov_user = GovUser.objects.get(id=user_id)
        except ExporterUser.DoesNotExist:
            raise PermissionDeniedError(USER_NOT_FOUND_ERROR)

        if gov_user.status == GovUserStatuses.DEACTIVATED:
            raise PermissionDeniedError(USER_DEACTIVATED_ERROR)

        return gov_user, hawk_receiver


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
            return HawkOnlyAuthentication().authenticate(request)


def _authenticate(request):
    """
    Raises a HawkFail exception if the passed request cannot be authenticated
    """

    if HAWK_AUTHENTICATION_ENABLED:
        return Receiver(
            _lookup_credentials,
            request.META["HTTP_HAWK_AUTHENTICATION"],
            # build_absolute_uri() returns 'http' which is incorrect since our clients communicate via https
            request.build_absolute_uri().replace("http", "https"),
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
