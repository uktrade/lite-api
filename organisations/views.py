from django.http import JsonResponse
from rest_framework import status
import json

from organisations.models import Organisation
from organisations.serializers import OrganisationSerializer
from users.libraries.CreateFirstAdminUser import CreateFirstAdminUser


def organisations_list(request):
    if request.method == "POST":
        name = request.POST.get('name')
        eori_number = request.POST.get('eori_number')
        sic_number = request.POST.get('sic_number')
        address = request.POST.get('address')
        email = request.POST.get('admin_user_email')

        new_organisation = Organisation(name=name,
                                        eori_number=eori_number,
                                        sic_number=sic_number,
                                        address=address)

        new_organisation.save()

        CreateFirstAdminUser(email, new_organisation)

        serializer = OrganisationSerializer(new_organisation)

        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
