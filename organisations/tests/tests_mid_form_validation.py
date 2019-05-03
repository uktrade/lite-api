import json
import uuid

from rest_framework import status

from addresses.models import Address
from organisations.models import Organisation, Site
from users.models import User
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase
from rest_framework.reverse import reverse
from django.urls import path, include
from reversion.models import Version


class RegisterBusinessValidationTests(APITestCase, URLPatternsTestCase):

    urlpatterns = [
        path('organisations/', include('organisations.urls'))
    ]

    client = APIClient

    def test_validate_organisation(self):
        self.name = "Big Scary Guns ltd"
        self.eori_number = "GB123456789000"
        self.sic_number = "2765"
        self.vat_number = "123456789"
        self.registration_number = "987654321"

        url = reverse('organisations:validate')
        data = {
            'organisation': {
                'name': self.name,
                'eori_number': self.eori_number,
                'sic_number': self.sic_number,
                'vat_number': self.vat_number,
                'registration_number': self.registration_number,
            },
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reject_invalid_organisation(self):
        url = reverse('organisations:validate')
        data = {
            'organisation': {
                'name': '',
                'eori_number': '',
                'sic_number': '',
                'vat_number': '',
                'registration_number': '',
            },
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_validate_site_and_address(self):
        # Site name
        self.site_name = "headquarters"

        # Address details
        self.country = "England"
        self.address_line_1 = "42 Industrial Estate"
        self.address_line_2 = "Queens Road"
        self.state = "Hertfordshire"
        self.zip_code = "AL1 4GT"
        self.city = "St Albans"

        url = reverse('organisations:validate')
        data = {
            # Site name
            'site': {
                'name': self.site_name,
                'country': self.country,
                'address_line_1': self.address_line_1,
                'address_line_2': self.address_line_2,
                'state': self.state,
                'zip_code': self.zip_code,
                'city': self.city,
            },
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reject_invalid_site_and_address(self):
        url = reverse('organisations:validate')
        data = {
            # Site name
            'site': {
                'name': '',
                'country': '',
                'address_line_1': '',
                'address_line_2': '',
                'state': '',
                'zip_code': '',
                'city': '',
            },
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_validate_user(self):
        # Site name
        self.site_name = "headquarters"

        # Address details
        self.country = "England"
        self.address_line_1 = "42 Industrial Estate"
        self.address_line_2 = "Queens Road"
        self.state = "Hertfordshire"
        self.zip_code = "AL1 4GT"
        self.city = "St Albans"

        # User details
        self.admin_user_first_name = "Trinity"
        self.admin_user_last_name = "Fishburne"
        self.admin_user_email = "trinity@bsg.com"
        self.password = "password123"
        self.reenter_password = "password123"

        url = reverse('organisations:validate')
        data = {
            'user': {
                'first_name': self.admin_user_first_name,
                'last_name': self.admin_user_last_name,
                'email': self.admin_user_email,
                'password': self.password,
                'reenter_password': self.reenter_password
            },
            'site': {
                'name': self.site_name,
                'country': self.country,
                'address_line_1': self.address_line_1,
                'address_line_2': self.address_line_2,
                'state': self.state,
                'zip_code': self.zip_code,
                'city': self.city,
            },
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reject_invalid_user(self):
        url = reverse('organisations:validate')
        data = {
            'user': {
                'first_name': '',
                'last_name': '',
                'email': '',
                'password': '',
                'reenter_password': '',
            },
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_key(self):
        url = reverse('organisations:validate')
        data = {'banana': 'banana'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = json.loads(response.content)
        self.assertEqual(response_data.get('errors'), 'Invalid key')