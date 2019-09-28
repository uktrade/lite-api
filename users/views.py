from django.db.models import Q
from django.http.response import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, generics
from rest_framework.exceptions import ParseError
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from cases.models import Notification
from conf.authentication import ExporterAuthentication, ExporterOnlyAuthentication
from conf.serializers import response_serializer
from goods.helpers import add_organisation_to_data
from users.libraries.user_to_token import user_to_token
from users.models import ExporterUser
from users.serializers import ExporterUserViewSerializer, ExporterUserCreateUpdateSerializer, NotificationSerializer


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

        token = user_to_token(user)
        return JsonResponse(data={'token': token,
                                  'first_name': user.first_name,
                                  'last_name': user.last_name,
                                  'lite_api_user_id': str(user.id)})


class UserList(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request):
        """
        Returns a list of Exporter users
        """
        return response_serializer(ExporterUserViewSerializer, obj=ExporterUser.objects.all(), many=True, response_name='users')

    @swagger_auto_schema(
        responses={
            400: 'JSON parse error'
        })
    def post(self, request):
        """
        Create Exporter within the same organisation that current user is logged into
        """
        data = JSONParser().parse(request)
        return response_serializer(ExporterUserCreateUpdateSerializer,
                                   data=data,
                                   response_name='user',
                                   pre_validation_actions=[
                                       add_organisation_to_data
                                   ])


class UserDetail(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        """
        Get user from pk
        """
        return response_serializer(ExporterUserViewSerializer, pk=pk, object_class=ExporterUser, response_name='user')

    @swagger_auto_schema(
        responses={
            400: 'JSON parse error'
        })
    def put(self, request, pk):
        """
        Update Exporter user
        """
        data = JSONParser().parse(request)
        return response_serializer(ExporterUserCreateUpdateSerializer,
                                   data=data,
                                   pk=pk,
                                   object_class=ExporterUser,
                                   response_name='user',
                                   partial=True)


class UserMeDetail(APIView):
    authentication_classes = (ExporterOnlyAuthentication,)
    """
    Get the user from request
    """

    def get(self, request):
        serializer = ExporterUserViewSerializer(request.user)
        return JsonResponse(data={'user': serializer.data})


class NotificationViewset(generics.ListAPIView):
    model = Notification
    serializer_class = NotificationSerializer
    authentication_classes = (ExporterAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Notification.objects.all()

    def get_queryset(self):
        organisation_id = self.request.META['HTTP_ORGANISATION_ID']

        # Get all notifications for the current user and organisation on License Application cases,
        # both those arising from case notes and those arising from ECJU queries
        queryset = Notification.objects \
            .filter(user=self.request.user) \
            .filter(Q(case_note__case__application__organisation_id=organisation_id) |
                    Q(case_note__case__query__organisation_id=organisation_id) |
                    Q(query__organisation__id=organisation_id) |
                    Q(ecju_query__case__application__organisation_id=organisation_id) |
                    Q(ecju_query__case__query__organisation_id=organisation_id))

        if self.request.GET.get('unviewed'):
            queryset = queryset.filter(viewed_at__isnull=True)

        return queryset
