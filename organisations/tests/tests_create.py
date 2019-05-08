import json
import uuid

from reversion.models import Version

from django.urls import path, include
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase

from organisations.models import Organisation, Site
from users.models import User


class OrganisationCreateTests(APITestCase, URLPatternsTestCase):
    urlpatterns = [
        path('organisations/', include('organisations.urls'))
    ]

    client = APIClient

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
        self.country = "England"
        self.address_line_1 = "42 Industrial Estate"
        self.address_line_2 = "Queens Road"
        self.state = "Hertfordshire"
        self.zip_code = "AL1 4GT"
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
                    'state': self.state,
                    'zip_code': self.zip_code,
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
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Organisation.objects.get().name, "Big Scary Guns ltd")
        self.assertEqual(Organisation.objects.get().eori_number, "GB123456789000")
        self.assertEqual(Organisation.objects.get().sic_number, "2765")
        self.assertEqual(Organisation.objects.get().vat_number, "123456789")
        self.assertEqual(Organisation.objects.get().registration_number, "987654321")
        self.assertEqual(User.objects.get().email, "trinity@bsg.com")
        self.assertEqual(User.objects.get().first_name, self.admin_user_first_name)
        self.assertEqual(User.objects.get().last_name, self.admin_user_last_name)
        self.assertEqual(Site.objects.get(name="Headquarters").address.address_line_1,
                         "42 Industrial Estate")
        self.assertEqual(Site.objects.get(name="Headquarters").name, "Headquarters")

        response_json = json.loads(response.content)
        organisation_id = response_json['organisation']['id']
        user_id = User.objects.get(email='trinity@bsg.com').id
        site_id = Organisation.objects.get(id=organisation_id).primary_site.id
        address_id = Organisation.objects.get(id=organisation_id).primary_site.address.id
        version_record = Version.objects.get(object_id=uuid.UUID(organisation_id))
        self.assertEqual(version_record.object.name, "Big Scary Guns ltd")
        self.assertEqual(version_record.object.eori_number, "GB123456789000")
        self.assertEqual(version_record.object.sic_number, "2765")
        self.assertEqual(version_record.object.vat_number, "123456789")
        self.assertEqual(version_record.object.registration_number, "987654321")
        self.assertEqual(Version.objects.get(object_id=user_id).object.email,
                         "trinity@bsg.com")
        self.assertEqual(Version.objects.get(object_id=address_id).object.address_line_1,
                         "42 Industrial Estate")
        self.assertEqual(Version.objects.get(object_id=site_id).object.name,
                         "Headquarters")

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
                    'state': None,
                    'zip_code': None,
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
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
