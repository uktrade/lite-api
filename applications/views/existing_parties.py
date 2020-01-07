from rest_framework.views import APIView

from conf.authentication import ExporterAuthentication
from conf.decorators import authorised_users
from users.models import ExporterUser


class ExistingParties(APIView):
    authentication_classes = (ExporterAuthentication,)

    @authorised_users(ExporterUser)
    def get(self, request, application):
        """
        Get existing parties created by the organisation
        """
        pass
