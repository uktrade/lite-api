from rest_framework import status
from rest_framework.reverse import reverse

from organisations.models import Organisation
from test_helpers.clients import DataTestClient
from users.libraries.get_user import get_users_from_organisation
from parameterized import parameterized


class OrganisationCreateTests(DataTestClient):

    url = reverse('organisations:organisations')

    def test_create_organisation_with_first_user(self):
        data = {
            'name': 'Lemonworld Co',
            'sub_type': 'commercial',
            'eori_number': 'GB123456789000',
            'sic_number': '2765',
            'vat_number': '123456789',
            'registration_number': '987654321',
            'site': {
                'name': 'Headquarters',
                'address': {
                    'address_line_1': '42 Industrial Estate',
                    'address_line_2': 'Queens Road',
                    'region': 'Hertfordshire',
                    'postcode': 'AL1 4GT',
                    'city': 'St Albans',
                    'country': 'GB',
                },
            },
            'user': {
                'first_name': 'Trinity',
                'last_name': 'Fishburne',
                'email': 'trinity@bsg.com'
            },
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        organisation = Organisation.objects.get(name=data['name'])
        exporter_user = get_users_from_organisation(organisation)[0]
        site = organisation.primary_site

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(organisation.name, data['name'])
        self.assertEqual(organisation.eori_number, data['eori_number'])
        self.assertEqual(organisation.sic_number, data['sic_number'])
        self.assertEqual(organisation.vat_number, data['vat_number'])
        self.assertEqual(organisation.registration_number, data['registration_number'])

        self.assertEqual(exporter_user.email, data['user']['email'])
        self.assertEqual(exporter_user.first_name, data['user']['first_name'])
        self.assertEqual(exporter_user.last_name, data['user']['last_name'])

        self.assertEqual(site.name, data['site']['name'])
        self.assertEqual(site.address.address_line_1, data['site']['address']['address_line_1'])
        self.assertEqual(site.address.address_line_2, data['site']['address']['address_line_2'])
        self.assertEqual(site.address.region, data['site']['address']['region'])
        self.assertEqual(site.address.postcode, data['site']['address']['postcode'])
        self.assertEqual(site.address.city, data['site']['address']['city'])
        self.assertEqual(str(site.address.country.id), data['site']['address']['country'])

    def test_cannot_create_organisation_with_invalid_data(self):
        data = {
            'name': None,
            'sub_type': 'commercial',
            'eori_number': None,
            'sic_number': None,
            'vat_number': None,
            'registration_number': None,
            'site': {
                'name': None,
                'address': {
                    'country': None,
                    'address_line_1': None,
                    'address_line_2': None,
                    'region': None,
                    'postcode': None,
                    'city': None,
                },
            },
            'user': {
                'first_name': None,
                'last_name': None,
                'email': None,
                'password': None,
            },
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @parameterized.expand([
        ['1234', '1234', '1234', ''],
        ['1234', '1234', '', '1234'],
        ['1234', '', '1234', '1234'],
        ['', '1234', '1234', '1234'],
    ])
    def test_create_organisation_missing_fields_failure(self, eori_number, vat_number, sic_number, registration_number):
        data = {
            'name': 'Lemonworld Co',
            'sub_type': 'commercial',
            'eori_number': eori_number,
            'sic_number': sic_number,
            'vat_number': vat_number,
            'registration_number': registration_number,
            'site': {
                'name': 'Headquarters',
                'address': {
                    'address_line_1': '42 Industrial Estate',
                    'address_line_2': 'Queens Road',
                    'region': 'Hertfordshire',
                    'postcode': 'AL1 4GT',
                    'city': 'St Albans',
                    'country': 'GB',
                },
            },
            'user': {
                'first_name': 'Trinity',
                'last_name': 'Fishburne',
                'email': 'trinity@bsg.com'
            },
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    @parameterized.expand([
        ['123467', '1231234'],  # With data
        ['', ''],  # without data
    ])
    def test_create_organisation_as_a_private_individual(self, eori_number, vat_number):
        data = {
            'sub_type': 'individual',
            'eori_number': eori_number,
            'vat_number': vat_number,
            'site': {
                'name': 'Headquarters',
                'address': {
                    'address_line_1': '42 Industrial Estate',
                    'address_line_2': 'Queens Road',
                    'region': 'Hertfordshire',
                    'postcode': 'AL1 4GT',
                    'city': 'St Albans',
                    'country': 'GB',
                },
            },
            'user': {
                'first_name': 'Trinity',
                'last_name': 'Fishburne',
                'email': 'trinity@bsg.com'
            },
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        organisation = Organisation.objects.get(name=data['user']['first_name'] + " " + data['user']['last_name'])
        exporter_user = get_users_from_organisation(organisation)[0]
        site = organisation.primary_site

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(organisation.name, data['user']['first_name'] + " " + data['user']['last_name'])
        self.assertEqual(organisation.eori_number, data['eori_number'])
        self.assertEqual(organisation.vat_number, data['vat_number'])

        self.assertEqual(exporter_user.email, data['user']['email'])
        self.assertEqual(exporter_user.first_name, data['user']['first_name'])
        self.assertEqual(exporter_user.last_name, data['user']['last_name'])

        self.assertEqual(site.name, data['site']['name'])
        self.assertEqual(site.address.address_line_1, data['site']['address']['address_line_1'])
        self.assertEqual(site.address.address_line_2, data['site']['address']['address_line_2'])
        self.assertEqual(site.address.region, data['site']['address']['region'])
        self.assertEqual(site.address.postcode, data['site']['address']['postcode'])
        self.assertEqual(site.address.city, data['site']['address']['city'])
        self.assertEqual(str(site.address.country.id), data['site']['address']['country'])