from rest_framework import authentication, exceptions

from gov_users.enums import GovUserStatuses
from gov_users.libraries.token_to_user_pk import token_to_user_pk
from users.models import ExporterUser, UserStatuses
from users.models import GovUser

EXPORTER_ID = 'HTTP_USER_ID'
GOV_USER_EMAIL_HEADER = 'HTTP_GOV_USER_EMAIL'
GOV_USER_TOKEN_HEADER = 'HTTP_GOV_USER_TOKEN'
EXPORTER_USER_EMAIL_HEADER = 'HTTP_EXPORTER_USER_EMAIL'
EXPORTER_USER_TOKEN_HEADER = 'HTTP_EXPORTER_USER_TOKEN'
USER_DEACTIVATED_ERROR = 'User has been deactivated'
USER_DOES_NOT_EXIST_ERROR = 'No such user with that identifier'


class ExporterAuthentication(authentication.BaseAuthentication):

    def authenticate(self, request):

        email = request.META.get(EXPORTER_USER_EMAIL_HEADER)
        token = request.META.get(EXPORTER_USER_TOKEN_HEADER)

        try:
            if token:
                user = ExporterUser.objects.get(pk=token_to_user_pk(token))
            else:
                user = ExporterUser.objects.get(email=email)
        except ExporterUser.DoesNotExist:
            raise exceptions.PermissionDenied(USER_DOES_NOT_EXIST_ERROR)

        if user.status == GovUserStatuses.DEACTIVATED:
            raise exceptions.PermissionDenied(USER_DEACTIVATED_ERROR)

        return user, None


class GovAuthentication(authentication.BaseAuthentication):

    def authenticate(self, request):
        email = request.META.get(GOV_USER_EMAIL_HEADER)
        token = request.META.get(GOV_USER_TOKEN_HEADER)

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
        email = request.META.get(EXPORTER_USER_EMAIL_HEADER)
        token = request.META.get(EXPORTER_USER_TOKEN_HEADER)

        exporter = email or token

        if exporter:
            try:
                if token:
                    user = ExporterUser.objects.get(pk=token_to_user_pk(token))
                else:
                    user = ExporterUser.objects.get(email=email)
            except ExporterUser.DoesNotExist:
                raise exceptions.PermissionDenied(USER_DOES_NOT_EXIST_ERROR)

            if user.status == GovUserStatuses.DEACTIVATED:
                raise exceptions.PermissionDenied(USER_DEACTIVATED_ERROR)

            return user, None
        else:
            email = request.META.get(GOV_USER_EMAIL_HEADER)
            token = request.META.get(GOV_USER_TOKEN_HEADER)

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
