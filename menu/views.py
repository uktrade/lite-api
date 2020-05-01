from django.http import JsonResponse
from rest_framework.views import APIView

from conf.authentication import GovAuthentication
from conf.constants import GovPermissions
from organisations.enums import OrganisationStatus
from organisations.models import Organisation


class MenuNotifications(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request):
        notifications = {
            "organisations": Organisation.objects.filter(status=OrganisationStatus.IN_REVIEW).count()
            if request.user.has_permission(GovPermissions.MANAGE_ORGANISATIONS)
            else 0
        }
        return JsonResponse(
            {"notifications": notifications, "has_notifications": any(value for value in notifications.values())}
        )
