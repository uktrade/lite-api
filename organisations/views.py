import uuid

from django.db import transaction
from django.http import JsonResponse
from django.http.response import Http404
from rest_framework import status
from rest_framework.parsers import JSONParser
import reversion

from addresses.libraries.CreateAddress import CreateAddress
from addresses.serializers import AddressBaseSerializer
from organisations.libraries.CreateSite import CreateSite
from organisations.models import Organisation, Site
from organisations.serializers import OrganisationInitialSerializer, OrganisationViewSerializer, SiteSerializer, \
    OrganisationUpdateSerializer
from users.libraries.CreateFirstAdminUser import CreateFirstAdminUser
from users.serializers import ViewUserSerializer, UserBaseSerializer


@transaction.atomic
def organisations_list(request):
    if request.method == "POST":
        with reversion.create_revision():
            data = JSONParser().parse(request)
            errors = {}
            address_data, site_data, organisation_data, user_data = split_data_into_entities(data)
            # This dummy uuid references the dummy address, site and organisation to satisfy the not
            # null constraints until the whole atomic transaction is complete
            dummy_uuid = uuid.UUID('00000000-0000-0000-0000-000000000000')

            organisation_data['primary_site'] = dummy_uuid
            organisation_serializer = OrganisationViewSerializer(data=organisation_data)
            if organisation_serializer.is_valid():
                organisation = organisation_serializer.save()
            else:
                errors['organisation'] = organisation_serializer.errors

            address_serializer = AddressBaseSerializer(data=address_data)
            if address_serializer.is_valid():
                address = address_serializer.save()
            else:
                errors['address'] = address_serializer.errors

            site_data['organisation'] = organisation.id
            site_data['address'] = address.id
            site_serializer = SiteSerializer(data=site_data)
            if site_serializer.is_valid():
                site = site_serializer.save()
            else:
                errors['site'] = site_serializer.errors

            organisation_update_data = {'primary_site': site.id}
            organisation_serializer = OrganisationUpdateSerializer(organisation, data=organisation_update_data, partial=True)
            if organisation_serializer.is_valid():
                organisation = organisation_serializer.save()
            else:
                errors['organisation'] = organisation_serializer.errors

            user_data['organisation'] = organisation.id
            user_serializer = UserBaseSerializer(data=user_data)
            if user_serializer.is_valid():
                user = user_serializer.save()
                user.set_password('password')
                user.save()

            else:
                errors['user'] = user_serializer.errors

            if errors == {}:
                return JsonResponse(data={'organisation': organisation_serializer.data,
                                          'user': user_serializer.data,
                                          'address': address_serializer.data,
                                          'site': site_serializer.data},
                                    status=status.HTTP_201_CREATED)
            else:
                return JsonResponse(data=errors, status=status.HTTP_400_BAD_REQUEST)

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
                'first_name': data['admin_user_first_name'],
                'last_name': data['admin_user_last_name'],
                'email': data['admin_user_email']
                }

    return address_data, site_data, organisation_data, user_data
