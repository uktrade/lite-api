from rest_framework import status
from rest_framework.reverse import reverse

from organisations.models import Organisation, Site
from test_helpers.clients import DataTestClient
from users.models import ExporterUser, UserOrganisationRelationship


class OrganisationCreateTests(DataTestClient):

    def test_create_organisation_with_first_user(self):
        self.name = "Big Scary Guns ltd"
        self.eori_number = "GB123456789000"
        self.sic_number = "2765"
        self.vat_number = "123456789"
        self.registration_number = "987654321"
        self.address = "London"

        # Site name
        self.site_name = "Headquarters"

        # Address details
        self.country = 'GB'
        self.address_line_1 = "42 Industrial Estate"
        self.address_line_2 = "Queens Road"
        self.region = "Hertfordshire"
        self.postcode = "AL1 4GT"
        self.city = "St Albans"

        # First admin user details
        self.admin_user_first_name = "Trinity"
        self.admin_user_last_name = "Fishburne"
        self.admin_user_email = "trinity@bsg.com"
        self.password = "password123"

        url = reverse('organisations:organisations')
        data = {
            'name': self.name,
            'eori_number': self.eori_number,
            'sic_number': self.sic_number,
            'vat_number': self.vat_number,
            'registration_number': self.registration_number,
            'site': {
                'name': self.site_name,
                'address': {
                    'country': self.country,
                    'address_line_1': self.address_line_1,
                    'address_line_2': self.address_line_2,
                    'region': self.region,
                    'postcode': self.postcode,
                    'city': self.city,
                },
            },
            'user': {
                'first_name': self.admin_user_first_name,
                'last_name': self.admin_user_last_name,
                'email': self.admin_user_email,
                'password': self.password
            },
        }
        response = self.client.post(url, data, **self.gov_headers)
        Organisation.objects.get(name='Org1').delete()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Organisation.objects.get().name, "Big Scary Guns ltd")
        self.assertEqual(Organisation.objects.get().eori_number, "GB123456789000")
        self.assertEqual(Organisation.objects.get().sic_number, "2765")
        self.assertEqual(Organisation.objects.get().vat_number, "123456789")
        self.assertEqual(Organisation.objects.get().registration_number, "987654321")
        self.assertEqual(ExporterUser.objects.get().email, "trinity@bsg.com")
        self.assertEqual(ExporterUser.objects.get().first_name, self.admin_user_first_name)
        self.assertEqual(ExporterUser.objects.get().last_name, self.admin_user_last_name)
        self.assertEqual(Site.objects.get(name="Headquarters").address.address_line_1,
                         "42 Industrial Estate")
        self.assertEqual(Site.objects.get(name="Headquarters").name, "Headquarters")

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
