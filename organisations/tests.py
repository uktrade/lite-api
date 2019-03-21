from rest_framework import status
from organisations.models import Organisation
from users.models import User
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase
from rest_framework.reverse import reverse
from django.urls import path, include


class OrganisationTests(APITestCase, URLPatternsTestCase):

    urlpatterns = [
        path('organisations/', include('organisations.urls'))
    ]

    client = APIClient

    def test_create_organisation_with_first_user(self):

        name="Big Scary Guns ltd"
        eori_number="GB123456789000"
        sic_number="2765"
        address="London"
        admin_user_email="trinity@bsg.com"

        url = reverse('organisations:organisations')
        data = {'name': name, 'eori_number': eori_number, 'sic_number': sic_number, 'address': address, 'admin_user_email': admin_user_email}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Organisation.objects.get().name, "Big Scary Guns ltd")
        self.assertEqual(Organisation.objects.get().eori_number, "GB123456789000")
        self.assertEqual(Organisation.objects.get().sic_number, "2765")
        self.assertEqual(Organisation.objects.get().address, "London")
        self.assertEqual(User.objects.get().email, "trinity@bsg.com")

    def test_create_invalid_organisation(self):
        url = '/organisations/'
        data = {'name': None, 'eori_number': None, 'sic_number': None, 'address': None,
                'admin_user_email': None}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
