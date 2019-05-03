import uuid

from django.http import JsonResponse
from rest_framework import status
from addresses.serializers import AddressBaseSerializer
from organisations.serializers import OrganisationUpdateSerializer, SiteSerializer, OrganisationViewSerializer, \
    OrganisationValidateFormSection, SiteValidateFormSection, UserValidateFormSection
from users.libraries.do_passwords_match import passwords_match
from users.serializers import UserBaseSerializer


def register_new_business(data):
    address_data, site_data, organisation_data, user_data = split_data_into_entities(data)
    # This dummy uuid references the dummy address, site and organisation to satisfy the not
    # null constraints until the whole atomic transaction is complete
    dummy_uuid = uuid.UUID('00000000-0000-0000-0000-000000000000')
    organisation = False
    organisation_update_data = False
    errors = {}

    organisation_data['primary_site'] = dummy_uuid
    organisation_serializer = OrganisationViewSerializer(data=organisation_data)
    if organisation_serializer.is_valid():
        organisation = organisation_serializer.save()
        site_data['organisation'] = organisation.id
    else:
        errors['organisation'] = organisation_serializer.errors

    address_serializer = AddressBaseSerializer(data=address_data)
    if address_serializer.is_valid():
        address = address_serializer.save()
        site_data['address'] = address.id
    else:
        errors['address'] = address_serializer.errors

    site_serializer = SiteSerializer(data=site_data)
    if site_serializer.is_valid():
        site = site_serializer.save()
        organisation_update_data = {'primary_site': site.id}
    else:
        errors['site'] = site_serializer.errors

    if organisation and organisation_update_data:
        organisation_serializer = OrganisationUpdateSerializer(organisation,
                                                               data=organisation_update_data,
                                                               partial=True)
        if organisation_serializer.is_valid():
            organisation = organisation_serializer.save()
            user_data['organisation'] = organisation.id
        else:
            errors['organisation'] = organisation_serializer.errors

    user_serializer = UserBaseSerializer(data=user_data)
    if user_serializer.is_valid():
        user = user_serializer.save()
        if user_data['password']:
            user.set_password(user_data['password'])
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


def split_data_into_entities(data):
    """
    Takes the response data from request and splits it into
    organisation, user, address and site information. Details
    of the field names are in the test_helper.
    """
    address_data = data.get('address')
    site_data = data.get('site')
    organisation_data = data.get('organisation')
    user_data = data.get('user')

    return address_data, site_data, organisation_data, user_data


def validate_form_section(data):
    errors = {}
    return_data = {}
    for key in data:
        if key not in ('organisation', 'site', 'user'):
            errors = {'errors': 'Invalid key'}
        else:
            if key == 'organisation':
                serializer = OrganisationValidateFormSection(data=data['organisation'])
                if serializer.is_valid():
                    return_data['organisation'] = serializer.data
                else:
                    errors['organisation'] = serializer.errors

            if key == 'site':
                serializer = SiteValidateFormSection(data=data['site'])
                if serializer.is_valid():
                    return_data['site'] = serializer.data
                else:
                    errors['site'] = serializer.errors

            if key == 'user':
                serializer = UserValidateFormSection(data=data['user'])
                if not passwords_match(data['user']['password'], data['user']['reenter_password']):
                    errors['reenter_password'] = 'Passwords do not match'
                if serializer.is_valid():
                    return_data['user'] = serializer.data
                else:
                    errors['user'] = serializer.errors

        if errors == {}:
            return JsonResponse(return_data, status=status.HTTP_200_OK)
        else:
            return JsonResponse(errors, status=status.HTTP_400_BAD_REQUEST)
