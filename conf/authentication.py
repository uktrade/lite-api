from rest_framework import authentication, exceptions

from gov_users.enums import GovUserStatuses
from gov_users.libraries.token_to_user import token_to_user_pk
from organisations.libraries.get_organisation import get_organisation_by_pk
from users.enums import UserStatuses
from users.libraries.get_user import get_user_by_pk, get_user_organisations
from users.models import UserOrganisationRelationship

GOV_USER_TOKEN_HEADER = 'HTTP_GOV_USER_TOKEN'

EXPORTER_USER_TOKEN_HEADER = 'HTTP_EXPORTER_USER_TOKEN'
ORGANISATION_ID = 'HTTP_ORGANISATION_ID'

USER_DEACTIVATED_ERROR = 'User has been deactivated'


class ExporterAuthentication(authentication.BaseAuthentication):

    def authenticate(self, request):
        """
        When given a user token and an organisation id, validate that the user belongs to the
        organisation and that they're allowed to access that organisation
        """
        exporter_user_token = request.META.get(EXPORTER_USER_TOKEN_HEADER)
        organisation_id = request.META.get(ORGANISATION_ID)

        exporter_user = get_user_by_pk(token_to_user_pk(exporter_user_token))
        organisation = get_organisation_by_pk(organisation_id)

        if organisation in get_user_organisations(exporter_user):
            user_organisation_relationship = UserOrganisationRelationship.objects.get(user=exporter_user,
                                                                                      organisation=organisation)

            if user_organisation_relationship.status == UserStatuses.DEACTIVATED:
                raise exceptions.PermissionDenied(USER_DEACTIVATED_ERROR)

            exporter_user.organisation = organisation

            return exporter_user, None

        raise exceptions.PermissionDenied('You don\'t belong to that organisation')


class ExporterOnlyAuthentication(authentication.BaseAuthentication):

    def authenticate(self, request):
        """
        When given a user token and an organisation id, validate that the user belongs to the
        organisation and that they're allowed to access that organisation
        """
        exporter_user_token = request.META.get(EXPORTER_USER_TOKEN_HEADER)
        exporter_user = get_user_by_pk(token_to_user_pk(exporter_user_token))

        return exporter_user, None


class GovAuthentication(authentication.BaseAuthentication):

    def authenticate(self, request):
        """
        When given a user token token validate that they're a government user
        and that their account is active
        """
        gov_user_token = request.META.get(GOV_USER_TOKEN_HEADER)

        gov_user = get_user_by_pk(token_to_user_pk(gov_user_token))

        if gov_user.status == GovUserStatuses.DEACTIVATED:
            raise exceptions.PermissionDenied(USER_DEACTIVATED_ERROR)

        return gov_user, None


class SharedAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        exporter_token = request.META.get(EXPORTER_USER_TOKEN_HEADER)

        if exporter_token:
            exporter_auth = ExporterAuthentication()
            return exporter_auth.authenticate(request)
        else:
            gov_auth = GovAuthentication()
            return gov_auth.authenticate(request)
