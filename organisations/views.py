from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from organisations.models import Organisation
from organisations.serializers import OrganisationSerializer, NewOrganisationRequestSerializer
from users.libraries.CreateFirstAdminUser import CreateFirstAdminUser


def organisations_list(request):
    if request.method == "POST":
        data = JSONParser().parse(request)
        serializer = NewOrganisationRequestSerializer(data=data)

        if serializer.is_valid():
            new_organisation = Organisation(name=serializer['name'].value,
                                            eori_number=serializer['eori_number'].value,
                                            sic_number=serializer['sic_number'].value,
                                            vat_number=serializer['vat_number'].value,
                                            address=serializer['address'].value)
            new_organisation.save()
            CreateFirstAdminUser(serializer['admin_user_email'].value, new_organisation)
            organisation_serializer = OrganisationSerializer(new_organisation)

            return JsonResponse(organisation_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return JsonResponse({'status': 'error', 'errors': serializer.errors, 'data': serializer.data},
                                 status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    if request.method == "GET":
        organisations = Organisation.objects.all()
        serializer = OrganisationSerializer(organisations, many=True)
        return JsonResponse(serializer.data, safe=False)
