from django.db import transaction
from django.http import JsonResponse
from django.http.response import Http404
from rest_framework.parsers import JSONParser
import reversion
from rest_framework.views import APIView

from organisations.libraries.register_new_business import register_new_business, validate_form_section
from organisations.models import Organisation
from organisations.serializers import OrganisationViewSerializer


@transaction.atomic
def organisations_list(request):
    if request.method == "POST":
        with reversion.create_revision():
            data = JSONParser().parse(request)
            return register_new_business(data)

    if request.method == "GET":
        organisations = Organisation.objects.all().order_by('name')
        view_serializer = OrganisationViewSerializer(organisations, many=True)
        return JsonResponse(data={'organisations': view_serializer.data},
                            safe=False)


def organisation_detail(request, pk):
    if request.method == "GET":
        try:
            organisation = Organisation.objects.get(pk=pk)
            view_serializer = OrganisationViewSerializer(organisation)
            return JsonResponse(data={'organisation': view_serializer.data})
        except Organisation.DoesNotExist:
            raise Http404


class Validate(APIView):
    """
    Validate organisation data
    """
    def post(self, request):
        data = JSONParser().parse(request)
        return validate_form_section(data)
