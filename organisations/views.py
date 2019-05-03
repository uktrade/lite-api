from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from organisations.libraries.get_organisation import get_organisation_by_pk
from organisations.models import Organisation
from organisations.serializers import OrganisationViewSerializer, OrganisationCreateSerializer


class OrganisationsList(APIView):
    """
    Get all/create organisations
    """
    def get(self, request):
        organisations = Organisation.objects.all().order_by('name')
        view_serializer = OrganisationViewSerializer(organisations, many=True)
        return JsonResponse(data={'organisations': view_serializer.data},
                            safe=False)

    @transaction.atomic
    def post(self, request):
        data = JSONParser().parse(request)
        serializer = OrganisationCreateSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'organisation': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrganisationsDetail(APIView):
    """
    Get an organisation by its primary key
    """
    def get(self, request, pk):
        organisation = get_organisation_by_pk(pk)
        view_serializer = OrganisationViewSerializer(organisation)
        return JsonResponse(data={'organisation': view_serializer.data})
