import reversion
from django.db import transaction
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import GovAuthentication, SharedAuthentication
from organisations.libraries.get_organisation import get_organisation_by_pk
from organisations.models import Organisation
from organisations.serializers import OrganisationViewSerializer, OrganisationCreateSerializer


class OrganisationsList(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request):
        """
        List all organisations
        """
        organisations = Organisation.objects.all().order_by('name')
        view_serializer = OrganisationViewSerializer(organisations, many=True)
        return JsonResponse(data={'organisations': view_serializer.data})

    @transaction.atomic
    @swagger_auto_schema(
        request_body=OrganisationCreateSerializer,
        responses={
            400: 'JSON parse error'
        })
    def post(self, request):
        """
        Create a new organisation
        """
        with reversion.create_revision():
            data = JSONParser().parse(request)
            if data.get('sub_type') and data['sub_type'] == 'individual':
                try:
                    data['name'] = data['user']['first_name'] + " " + data['user']['last_name']
                except AttributeError:
                    pass
                except KeyError:
                    pass
            serializer = OrganisationCreateSerializer(data=data)

            if serializer.is_valid():
                serializer.save()
                return JsonResponse(data={'organisation': serializer.data},
                                    status=status.HTTP_201_CREATED)

            return JsonResponse(data={'errors': serializer.errors},
                                status=status.HTTP_400_BAD_REQUEST)


class OrganisationsDetail(APIView):
    authentication_classes = (SharedAuthentication,)
    """
    Get an organisation by its primary key
    """
    def get(self, request, pk):
        organisation = get_organisation_by_pk(pk)
        view_serializer = OrganisationViewSerializer(organisation)
        return JsonResponse(data={'organisation': view_serializer.data})
