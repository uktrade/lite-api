from django.http import JsonResponse
from django.http.response import Http404
from rest_framework import status
from rest_framework.parsers import JSONParser
import reversion

from organisations.models import Organisation
from organisations.serializers import OrganisationInitialSerializer, OrganisationViewSerializer
from users.libraries.CreateFirstAdminUser import CreateFirstAdminUser


def organisations_list(request):
    if request.method == "POST":
        with reversion.create_revision():
            data = JSONParser().parse(request)
            serializer = OrganisationInitialSerializer(data=data)
            serializer2 = OrganisationViewSerializer(data=data)

            if serializer.is_valid() and serializer2.is_valid():
                new_organisation = serializer2.save()

                # Create an admin for that company
                CreateFirstAdminUser(serializer['admin_user_email'].value, new_organisation)

                return JsonResponse(data={'status': 'success', 'organisation': serializer2.data},
                                    status=status.HTTP_201_CREATED)
            else:
                return JsonResponse(data={'status': 'error', 'errors': serializer.errors},
                                    status=status.HTTP_422_UNPROCESSABLE_ENTITY)

            # Store some version meta-information.
            # reversion.set_user(request.user)
            # reversion.set_comment("Created Organization Revision")

    if request.method == "GET":
        organisations = Organisation.objects.all().order_by('name')
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
