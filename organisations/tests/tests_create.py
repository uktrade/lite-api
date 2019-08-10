from rest_framework import status
from rest_framework.reverse import reverse

from organisations.models import Organisation
from test_helpers.clients import DataTestClient
from users.models import ExporterUser


class OrganisationCreateTests(DataTestClient):

    def test_create_organisation_with_first_user(self):
        name = 'New Organisation'
        eori_number = 'GB123456789000'
        sic_number = '2765'
        vat_number = '123456789'
        registration_number = '987654321'
        address = 'London'

        # Site name
        site_name = 'Headquarters'

        # Address details
        country = 'GB'
        address_line_1 = '42 Industrial Estate'
        address_line_2 = 'Queens Road'
        region = 'Hertfordshire'
        postcode = 'AL1 4GT'
        city = 'St Albans'

        # First admin user details
        admin_user_first_name = 'Trinity'
        admin_user_last_name = 'Fishburne'
        admin_user_email = 'trinity@bsg.com'
        password = 'password123'

        url = reverse('organisations:organisations')
        data = {
            'name': name,
            'eori_number': eori_number,
            'sic_number': sic_number,
            'vat_number': vat_number,
            'registration_number': registration_number,
            'site': {
                'name': site_name,
                'address': {
                    'country': country,
                    'address_line_1': address_line_1,
                    'address_line_2': address_line_2,
                    'region': region,
                    'postcode': postcode,
                    'city': city,
                },
            },
            'user': {
                'first_name': admin_user_first_name,
                'last_name': admin_user_last_name,
                'email': admin_user_email
            },
        }
        response = self.client.post(url, data, **self.gov_headers)

        organisation = Organisation.objects.filter(name=name)[0]
        exporter_user = ExporterUser.objects.filter(organisation=organisation)[0]
        site = organisation.primary_site

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(organisation.name, name)
        self.assertEqual(organisation.eori_number, 'GB123456789000')
        self.assertEqual(organisation.sic_number, '2765')
        self.assertEqual(organisation.vat_number, '123456789')
        self.assertEqual(organisation.registration_number, '987654321')
        self.assertEqual(exporter_user.email, 'trinity@bsg.com')
        self.assertEqual(exporter_user.first_name, admin_user_first_name)
        self.assertEqual(exporter_user.last_name, admin_user_last_name)
        self.assertEqual(site.address.address_line_1, '42 Industrial Estate')
        self.assertEqual(site.name, 'Headquarters')

    def tests_errors_are_send_from_failed_create(self):
        url = reverse('organisations:organisations')
        data = {
            'name': None,
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
        response = self.client.post(url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
