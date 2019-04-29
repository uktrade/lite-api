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
            create_serializer = OrganisationInitialSerializer(data=data)
            view_serializer = OrganisationViewSerializer(data=data)

            if create_serializer.is_valid() and view_serializer.is_valid():
                new_organisation = view_serializer.save()

                # Create an admin for that company
                CreateFirstAdminUser(create_serializer['admin_user_email'].value, new_organisation)

                return JsonResponse(data={'organisation': view_serializer.data},
                                    status=status.HTTP_201_CREATED)
            else:
                return JsonResponse(data={'errors': create_serializer.errors},
                                    status=status.HTTP_422_UNPROCESSABLE_ENTITY)

            # Store some version meta-information.
            # reversion.set_user(request.user)
            # reversion.set_comment("Created Organization Revision")

    if request.method == "GET":
        organisations = Organisation.objects.all().order_by('name')
        view_serializer = OrganisationViewSerializer(organisations, many=True)
        return JsonResponse(data={'status': 'success', 'organisations': view_serializer.data},
                            safe=False)


def organisation_detail(request, pk):
    if request.method == "GET":
        try:
            organisation = Organisation.objects.get(pk=pk)
            view_serializer = OrganisationViewSerializer(organisation)
            return JsonResponse(data={'organisation': view_serializer.data})
        except Organisation.DoesNotExist:
            raise Http404
