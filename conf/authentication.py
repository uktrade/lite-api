import logging

from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from mohawk import Receiver
from mohawk.exc import HawkFail, AlreadyProcessed
from rest_framework import authentication

from conf import settings
from conf.exceptions import PermissionDeniedError
from gov_users.enums import GovUserStatuses
from organisations.enums import OrganisationType
from organisations.libraries.get_organisation import get_organisation_by_pk
from users.enums import UserStatuses
from users.libraries.get_user import get_user_by_pk, get_user_organisations
from users.libraries.token_to_user import token_to_user_pk
from users.models import UserOrganisationRelationship

GOV_USER_TOKEN_HEADER = "HTTP_GOV_USER_TOKEN"  # nosec

EXPORTER_USER_TOKEN_HEADER = "HTTP_EXPORTER_USER_TOKEN"  # nosec
ORGANISATION_ID = "HTTP_ORGANISATION_ID"

USER_DEACTIVATED_ERROR = "User has been deactivated"

ORGANISATION_DEACTIVATED_ERROR = "Organisation is not activated"


class ExporterAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        """
        When given a user token and an organisation id, validate that the user belongs to the
        organisation and that they're allowed to access that organisation
        """

        # First, establish that the request has come from an authorised LITE API client
        # by checking that the request is correctly Hawk signed
        try:
            hawk_receiver = _authorise(request)
        except HawkFail as e:
            logging.warning(f"Failed HAWK authentication {e}")
            raise e

        if request.META.get(EXPORTER_USER_TOKEN_HEADER):
            exporter_user_token = request.META.get(EXPORTER_USER_TOKEN_HEADER)
        else:
            raise PermissionDeniedError("You must supply the correct token in your headers.")

        organisation_id = request.META.get(ORGANISATION_ID)

        exporter_user = get_user_by_pk(token_to_user_pk(exporter_user_token))
        organisation = get_organisation_by_pk(organisation_id)

        if organisation in get_user_organisations(exporter_user):
            user_organisation_relationship = UserOrganisationRelationship.objects.get(
                user=exporter_user, organisation=organisation
            )

            if not organisation.is_active():
                raise PermissionDeniedError(ORGANISATION_DEACTIVATED_ERROR)

            if user_organisation_relationship.status == UserStatuses.DEACTIVATED:
                raise PermissionDeniedError(USER_DEACTIVATED_ERROR)

            exporter_user.organisation = organisation

            return exporter_user, hawk_receiver

        raise PermissionDeniedError("You don't belong to that organisation")


class HmrcExporterAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        """
        When given a user token and an organisation id, validate that the user belongs to the
        organisation and that they're allowed to access that organisation
        """

        # First, establish that the request has come from an authorised LITE API client
        # by checking that the request is correctly Hawk signed
        try:
            hawk_receiver = _authorise(request)
        except HawkFail as e:
            logging.warning(f"Failed HAWK authentication {e}")
            raise e

        if request.META.get(EXPORTER_USER_TOKEN_HEADER):
            exporter_user_token = request.META.get(EXPORTER_USER_TOKEN_HEADER)
        else:
            raise PermissionDeniedError("You must supply the correct token in your headers.")

        organisation_id = request.META.get(ORGANISATION_ID)

        exporter_user = get_user_by_pk(token_to_user_pk(exporter_user_token))
        organisation = get_organisation_by_pk(organisation_id)

        if organisation.type != OrganisationType.HMRC:
            raise PermissionDeniedError("You don't belong to an HMRC organisation")

        if organisation in get_user_organisations(exporter_user):
            user_organisation_relationship = UserOrganisationRelationship.objects.get(
                user=exporter_user, organisation=organisation
            )

            if user_organisation_relationship.status == UserStatuses.DEACTIVATED:
                raise PermissionDeniedError(USER_DEACTIVATED_ERROR)

            exporter_user.organisation = organisation

            return exporter_user, hawk_receiver

        raise PermissionDeniedError("You don't belong to that organisation")


class ExporterOnlyAuthentication(authentication.BaseAuthentication):
    """
    Authenticates an exporter user without their organisation
    """

    def authenticate(self, request):
        """
        When given a user token, validate that the user exists
        """

        # First, establish that the request has come from an authorised LITE API client
        # by checking that the request is correctly Hawk signed
        try:
            hawk_receiver = _authorise(request)
        except HawkFail as e:
            logging.warning(f"Failed HAWK authentication {e}")
            raise e

        exporter_user_token = request.META.get(EXPORTER_USER_TOKEN_HEADER)
        exporter_user = get_user_by_pk(token_to_user_pk(exporter_user_token))

        return exporter_user, hawk_receiver


class HawkOnlyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        """
        When given a user token, validate that the user exists
        """

        # First, establish that the request has come from an authorised LITE API client
        # by checking that the request is correctly Hawk signed
        try:
            hawk_receiver = _authorise(request)
        except HawkFail as e:
            logging.warning(f"Failed HAWK authentication {e}")
            raise e

        return None, hawk_receiver


class GovAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        """
        When given a user token token validate that they're a government user
        and that their account is active
        """

        # First, establish that the request has come from an authorised LITE API client
        # by checking that the request is correctly Hawk signed
        try:
            hawk_receiver = _authorise(request)
        except HawkFail as e:
            logging.warning(f"Failed HAWK authentication {e}")
            raise e

        if request.META.get(GOV_USER_TOKEN_HEADER):
            gov_user_token = request.META.get(GOV_USER_TOKEN_HEADER)
        else:
            raise PermissionDeniedError("You must supply the correct token in your headers.")

        gov_user = get_user_by_pk(token_to_user_pk(gov_user_token))

        if gov_user.status == GovUserStatuses.DEACTIVATED:
            raise PermissionDeniedError(USER_DEACTIVATED_ERROR)

        return gov_user, hawk_receiver


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


def _authorise(request):
    """
    Raises a HawkFail exception if the passed request cannot be authenticated
    """
    return Receiver(
        _lookup_credentials,
        request.META["HTTP_AUTHORIZATION"],
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


def sign_rendered_response(request, response):
    if hasattr(request, "auth") and isinstance(request.auth, Receiver):
        response["Server-Authorization"] = request.auth.respond(
            content=response.content, content_type=response["Content-Type"],
        )

    return response
