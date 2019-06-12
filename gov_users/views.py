from django.http import JsonResponse

from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from gov_users.enums import GovUserStatuses
from gov_users.models import GovUser
from gov_users.serializers import GovUserSerializer


class AuthenticateGovUser(APIView):
    permission_classes = (AllowAny,)
    """
    Authenticate user
    """
    def post(self, request, *args, **kwargs):
        data = JSONParser().parse(request)
        email = data.get('email')
        first_name = data.get('first_name')
        last_name = data.get('last_name')

        try:
            user = GovUser.objects.get(email=email)

            # Update the user's first and last names
            user.first_name = first_name
            user.last_name = last_name
            user.save()
        except GovUser.DoesNotExist:
            return JsonResponse(data={'errors': 'User not found'},
                                status=status.HTTP_403_FORBIDDEN)

        if user.status == GovUserStatuses.DEACTIVATED:
            return JsonResponse(data={'errors': 'User not found'},
                                status=status.HTTP_403_FORBIDDEN)

        serializer = GovUserSerializer(user)
        return JsonResponse(data={'gov_user': serializer.data})
