from django.http import JsonResponse
from django.http.response import Http404
from django.shortcuts import redirect
from django.urls import reverse_lazy
from rest_framework import status
from rest_framework.parsers import JSONParser

from organisations.models import Organisation
from organisations.serializers import OrganisationInitialSerializer, OrganisationViewSerializer
from users.libraries.CreateFirstAdminUser import CreateFirstAdminUser


def organisations_list(request):
    if request.method == "POST":
        data = JSONParser().parse(request)
        serializer = OrganisationInitialSerializer(data=data)
        serializer2 = OrganisationViewSerializer(data=data)

        if serializer.is_valid() and serializer2.is_valid():
            new_organisation = serializer2.save()

            # Create an admin for that company
            CreateFirstAdminUser(serializer['admin_user_email'].value, new_organisation)

            return JsonResponse(data={'status': 'success', 'organisation': serializer.data},
                                status=status.HTTP_201_CREATED)
        else:
            return JsonResponse(data={'status': 'error', 'errors': serializer.errors},
                                status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    if request.method == "GET":
        organisations = Organisation.objects.all()
        serializer = OrganisationViewSerializer(organisations, many=True)
        return JsonResponse(data={'status': 'success', 'organisations': serializer.data},
                            safe=False)


def organisation_detail(request, pk):
    if request.method == "GET":
        try:
            organisation = Organisation.objects.get(pk=pk)
            serializer = OrganisationViewSerializer(organisation)
            return JsonResponse(data={'status': 'success', 'organisation': serializer.data})
        except Organisation.DoesNotExist:
            raise Http404
