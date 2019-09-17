import json

import reversion
from django.db.models import Q
from django.http.response import JsonResponse, Http404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, generics
from rest_framework.exceptions import ParseError
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from addresses.models import Address
from cases.models import Notification
from conf.authentication import ExporterAuthentication, ExporterOnlyAuthentication
from conf.settings import env
from organisations.libraries.get_organisation import get_organisation_by_user
from organisations.models import Organisation, Site
from static.countries.helpers import get_country
from users.enums import UserStatuses
from users.libraries.get_user import get_user_by_pk
from users.libraries.user_to_token import user_to_token
from users.models import ExporterUser, UserOrganisationRelationship
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
        serializer = ExporterUserViewSerializer(ExporterUser.objects.all(), many=True)
        return JsonResponse(data={'users': serializer.data})

    @swagger_auto_schema(
        responses={
            400: 'JSON parse error'
        })
    def post(self, request):
        """
        Create Exporter within the same organisation that current user is logged into
        """
        organisation = get_organisation_by_user(request.user)

        data = JSONParser().parse(request)
        data['organisation'] = organisation.id
        serializer = ExporterUserCreateUpdateSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'user': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class UserDetail(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        """
        Get user from pk
        """
        user = get_user_by_pk(pk)

        serializer = ExporterUserViewSerializer(user)
        return JsonResponse(data={'user': serializer.data})

    @swagger_auto_schema(
        responses={
            400: 'JSON parse error'
        })
    def put(self, request, pk):
        """
        Update Exporter user
        """
        user = get_user_by_pk(pk)
        data = JSONParser().parse(request)

        with reversion.create_revision():
            serializer = ExporterUserCreateUpdateSerializer(user, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse(data={'user': serializer.data},
                                    status=status.HTTP_200_OK)

            return JsonResponse(data={'errors': serializer.errors},
                                status=400)


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


class TestData(APIView):

    def get(self, request):
        """
        Generate test data
        """
        if not env('DEBUG'):
            raise Http404

        if Organisation.objects.count() == 0:
            organisation = Organisation(name='Lemonworld Co',
                                        eori_number='123',
                                        sic_number='123',
                                        vat_number='123',
                                        registration_number='123')
            organisation.save()

            address = Address(address_line_1='42 Road',
                              address_line_2='',
                              country=get_country('GB'),
                              city='London',
                              region='Buckinghamshire',
                              postcode='E14QW')
            address.save()
            site = Site(name='Lemonworld HQ',
                        organisation=organisation,
                        address=address)
            site.save()

            organisation.primary_site = site
            organisation.save()
        else:
            organisation = Organisation.objects.all().first()

        for email in json.loads(env('SEED_USERS')):
            if ExporterUser.objects.filter(email=email).count() == 0:
                first_name = email.split('.')[0]
                last_name = email.split('.')[1].split('@')[0]

                exporter_user = ExporterUser(email=email,
                                             first_name=first_name,
                                             last_name=last_name)
                exporter_user.save()

                UserOrganisationRelationship(user=exporter_user,
                                             organisation=organisation).save()
                exporter_user.status = UserStatuses.ACTIVE

        return JsonResponse({'status': 'success',
                             'report': str(ExporterUser.objects.count()) + ' in the system.'})
