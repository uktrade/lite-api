import reversion
from django.db import transaction
from django.http import JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from organisations.libraries.get_organisation import get_organisation_by_pk
from organisations.libraries.register_new_business import register_new_business, validate_form_section
from organisations.models import Organisation
from organisations.serializers import OrganisationViewSerializer


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
        with reversion.create_revision():
            data = JSONParser().parse(request)
            return register_new_business(data)


class OrganisationsDetail(APIView):
    """
    Get an organisation by its primary key
    """
    def get(self, request, pk):
        organisation = get_organisation_by_pk(pk)
        view_serializer = OrganisationViewSerializer(organisation)
        return JsonResponse(data={'organisation': view_serializer.data})


class Validate(APIView):
    """
    Validate organisation data
    """
    def post(self, request):
        data = JSONParser().parse(request)
        return validate_form_section(data)
