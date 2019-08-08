import reversion
from django.http.response import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.exceptions import ParseError
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from cases.models import Notification
from conf.authentication import ExporterAuthentication
from gov_users.enums import GovUserStatuses
from gov_users.libraries.user_to_token import user_to_token
from organisations.libraries.get_organisation import get_organisation_by_user
from users.libraries.get_user import get_user_by_pk
from users.libraries.user_is_trying_to_change_own_status import user_is_trying_to_change_own_status
from users.models import ExporterUser
from users.serializers import ExporterUserUpdateSerializer, ExporterUserCreateSerializer, NotificationsSerializer, \
    ExporterUserViewSerializer, ClcNotificationsSerializer


class AuthenticateExporterUser(APIView):
    """
        Authenticate user
        """
    permission_classes = (AllowAny,)

    @swagger_auto_schema(
        responses={
            400: 'JSON parse error',
            403: 'Forbidden'
        })
    def post(self, request, *args, **kwargs):
        """
        Takes user details from sso and checks them against our whitelisted users
        Returns a token which is just our ID for the user
        """
        try:
            data = JSONParser().parse(request)
        except ParseError:
            return JsonResponse(data={'errors': 'Invalid Json'},
                                status=status.HTTP_400_BAD_REQUEST)
        email = data.get('email')

        try:
            user = ExporterUser.objects.get(email=email)
        except ExporterUser.DoesNotExist:
            return JsonResponse(data={'errors': 'User not found'},
                                status=status.HTTP_403_FORBIDDEN)

        if user.status == GovUserStatuses.DEACTIVATED:
            return JsonResponse(data={'errors': 'User not found'},
                                status=status.HTTP_403_FORBIDDEN)

        token = user_to_token(user)
        return JsonResponse(data={'token': token, 'first_name': user.first_name, 'last_name': user.last_name, 'lite_api_user_id': str(user.id)})


class UserList(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request):
        organisation = get_organisation_by_user(request.user)
        serializer = ExporterUserViewSerializer(ExporterUser.objects.filter(organisation=organisation), many=True)
        return JsonResponse(data={'users': serializer.data})

    def post(self, request):
        organisation = get_organisation_by_user(request.user)

        data = JSONParser().parse(request)
        data['organisation'] = organisation.id
        serializer = ExporterUserCreateSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'user': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class UserDetail(APIView):
    authentication_classes = (ExporterAuthentication,)
    """
    Get user from pk
    """
    def get(self, request, pk):
        user = get_user_by_pk(pk)

        serializer = ExporterUserViewSerializer(user)
        return JsonResponse(data={'user': serializer.data})

    def put(self, request, pk):
        user = get_user_by_pk(pk)
        data = JSONParser().parse(request)

        if 'status' in data.keys():
            if user_is_trying_to_change_own_status(user.id, request.user.id):
                return JsonResponse(data={'errors': 'A user cannot change their own status'},
                                    status=status.HTTP_400_BAD_REQUEST)

        with reversion.create_revision():
            for key in list(data.keys()):
                if data[key] is '':
                    del data[key]

            serializer = ExporterUserUpdateSerializer(user, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse(data={'user': serializer.data},
                                    status=status.HTTP_200_OK)

            return JsonResponse(data={'errors': serializer.errors},
                                status=400)


class NotificationViewset(viewsets.ModelViewSet):
    model = Notification
    serializer_class = NotificationsSerializer
    authentication_classes = (ExporterAuthentication,)
    permission_classes = (IsAuthenticated, )
    queryset = Notification.objects.all()

    def get_queryset(self):
        # Get queryset using dunder expression to go across relationships (so note_id on Notification table
        # join to Case Note table join to Cases table and see if clc_query is null)
        queryset = Notification.objects.filter(user=self.request.user, note__case__clc_query_id__isnull=True)
        if self.request.GET.get('unviewed'):
            queryset = queryset.filter(viewed_at__isnull=True)

        return queryset


class ClcNotificationViewset(viewsets.ModelViewSet):
    model = Notification
    serializer_class = ClcNotificationsSerializer
    authentication_classes = (ExporterAuthentication,)
    permission_classes = (IsAuthenticated, )
    queryset = Notification.objects.all()

    def get_queryset(self):
        # Get queryset using dunder expression to go across relationships (so note_id on Notification table
        # join to Case Note table join to Cases table and see if application_id is null)
        queryset = Notification.objects.filter(user=self.request.user, note__case__application_id__isnull=True)
        if self.request.GET.get('unviewed'):
            queryset = queryset.filter(viewed_at__isnull=True)

        return queryset


class UserMeDetail(APIView):
    authentication_classes = (ExporterAuthentication,)
    """
    Get the user from request
    """
    def get(self, request):
        serializer = ExporterUserViewSerializer(request.user)
        return JsonResponse(data={'user': serializer.data})
