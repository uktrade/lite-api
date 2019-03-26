from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser

from organisations.models import Organisation
from organisations.serializers import OrganisationCreateSerializer, OrganisationViewSerializer
from users.libraries.CreateFirstAdminUser import CreateFirstAdminUser


def organisations_list(request):
    if request.method == "POST":
        data = JSONParser().parse(request)
        serializer = OrganisationCreateSerializer(data=data)

        if serializer.is_valid():
            new_organisation = serializer.save()

            # Create an admin for that company
            CreateFirstAdminUser(serializer['admin_user_email'].value, new_organisation)

            return JsonResponse(OrganisationViewSerializer(data=data).data,
                                status=status.HTTP_201_CREATED)
        else:
            return JsonResponse(data={'status': 'error', 'errors': serializer.errors},
                                status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    if request.method == "GET":
        organisations = Organisation.objects.all()
        serializer = OrganisationViewSerializer(organisations, many=True)
        return JsonResponse(data={'status': 'success', 'drafts': serializer.data},
                            safe=False)
