from django.http import JsonResponse
from django.http.response import Http404
from rest_framework import status
from rest_framework.parsers import JSONParser
import reversion

from addresses.libraries.CreateAddress import CreateAddress
from organisations.libraries.CreateSite import CreateSite
from organisations.models import Organisation
from organisations.serializers import OrganisationInitialSerializer, OrganisationViewSerializer
from users.libraries.CreateFirstAdminUser import CreateFirstAdminUser


def organisations_list(request):
    if request.method == "POST":
        with reversion.create_revision():
            data = JSONParser().parse(request)
            create_serializer = OrganisationInitialSerializer(data=data)
            view_serializer = OrganisationViewSerializer(data=data)
            address_data, site_data, organisation_data, user_data = split_data_into_entities(data)

            if create_serializer.is_valid() and create_user_serilizer.is_valid() and :
                address = CreateAddress(
                    country=create_serializer['country'].value,
                    address_line_1=create_serializer['address_line_1'].value,
                    address_line_2=create_serializer['address_line_2'].value,
                    state=create_serializer['state'].value,
                    zip_code=create_serializer['zip_code'].value,
                    city=create_serializer['city'].value,
                )

                site = CreateSite(name=create_serializer['site_name'],
                                  address=address)
                data['primary_site'] = str(site.id)

                new_organisation = view_serializer.save()

                # Create an admin for that company
                CreateFirstAdminUser(email=create_serializer['admin_user_email'].value,
                                     first_name=create_serializer['admin_user_first_name'].value,
                                     last_name=create_serializer['admin_user_last_name'].value,
                                     organisation=new_organisation)

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

def split_data_into_entities(data):
    """
    Takes the resposne data from request and splits it into
    organisation, user, address and site information
    :return:
    """
    address_data = {
                    'country': data['country'],
                    'address_line_1': data['address_line_1'],
                    'address_line_2': data['address_line_2'],
                    'state': data['state'],
                    'zip_code': data['zip_code'],
                    'city': data['city']
                    }

    site_data = {'name': data['site_name']}

    organisation_data = {
                        'name': data['name'],
                        'eori_number': data['eori_number'],
                        'sic_number': data['sic_number'],
                        'vat_number': data['vat_number'],
                        'registration_number': data['registration_number'],
                        }

    user_data = {
                'admin_user_first_name': data['admin_user_first_name'],
                'admin_user_last_name': data['admin_user_last_name'],
                'admin_user_email': data['admin_user_email']
                }

    return address_data, site_data, organisation_data, user_data
