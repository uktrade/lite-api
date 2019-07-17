from rest_framework import authentication, exceptions

from gov_users.enums import GovUserStatuses
from gov_users.libraries.token_to_user_pk import token_to_user_pk
from users.models import GovUser
from users.models import ExporterUser, UserStatuses


EXPORTER_ID = 'HTTP_USER_ID'
USER_EMAIL_HEADER = 'HTTP_GOV_USER_EMAIL'
USER_TOKEN_HEADER = 'HTTP_GOV_USER_TOKEN'
USER_DEACTIVATED_ERROR = 'User has been deactivated'
USER_DOES_NOT_EXIST_ERROR = 'No such user with that identifier'


class PkAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        pk = request.META.get(EXPORTER_ID)
        try:
            user = ExporterUser.objects.get(pk=pk)
        except ExporterUser.DoesNotExist:
            raise exceptions.AuthenticationFailed('No such user with that ID')

        if user.status == UserStatuses.DEACTIVATED:
            raise exceptions.PermissionDenied('User has been deactivated')

        return user, None


class GovAuthentication(authentication.BaseAuthentication):

    def authenticate(self, request):
        email = request.META.get(USER_EMAIL_HEADER)
        token = request.META.get(USER_TOKEN_HEADER)

        try:
            if token:
                user = GovUser.objects.get(pk=token_to_user_pk(token))
            else:
                user = GovUser.objects.get(email=email)
        except GovUser.DoesNotExist:
            raise exceptions.PermissionDenied(USER_DOES_NOT_EXIST_ERROR)

        if user.status == GovUserStatuses.DEACTIVATED:
            raise exceptions.PermissionDenied(USER_DEACTIVATED_ERROR)

        return user, None


class SharedAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        pk = request.META.get(EXPORTER_ID)

        if pk:
            try:
                user = ExporterUser.objects.get(pk=pk)
            except ExporterUser.DoesNotExist:
                raise exceptions.AuthenticationFailed('No such user with that ID')

            if user.status == UserStatuses.DEACTIVATED:
                raise exceptions.PermissionDenied('User has been deactivated')

            return user, None
        else:
            email = request.META.get(USER_EMAIL_HEADER)
            token = request.META.get(USER_TOKEN_HEADER)

            try:
                if token:
                    user = GovUser.objects.get(pk=token_to_user_pk(token))
                else:
                    user = GovUser.objects.get(email=email)
            except GovUser.DoesNotExist:
                raise exceptions.PermissionDenied(USER_DOES_NOT_EXIST_ERROR)

            if user.status == GovUserStatuses.DEACTIVATED:
                raise exceptions.PermissionDenied(USER_DEACTIVATED_ERROR)

            return user, None
