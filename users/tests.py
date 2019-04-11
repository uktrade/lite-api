import json

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase, URLPatternsTestCase, APIClient

from organisations.models import Organisation
from users.models import User
from django.urls import path, include


class UserTests(APITestCase, URLPatternsTestCase):

    urlpatterns = [
        path('users/', include('users.urls')),
    ]

    client = APIClient()

    def test_user_model(self):
        new_organisation = Organisation(name="Big Scary Guns ltd",
                                        eori_number="GB123456789000",
                                        sic_number="2765",
                                        vat_number="123456789",
                                        registration_number="987654321",
                                        address="London")

        new_user = User(email="trinity@bsg.com",
                        password="trinity@bsg.com",
                        organisation=new_organisation)

        new_organisation.save()
        new_user.save()
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().email, 'trinity@bsg.com')
        self.assertEqual(User.objects.get().password, 'trinity@bsg.com')
        self.assertEqual(User.objects.get().organisation, new_organisation)

    def test_super_simple_authentication(self):
        new_organisation = Organisation(name="Big Scary Guns ltd",
                                        eori_number="GB123456789000",
                                        sic_number="2765",
                                        vat_number="123456789",
                                        registration_number="987654321",
                                        address="London")

        new_user = User(email="trinity@bsg.com",
                        password="trinity@bsg.com",
                        organisation=new_organisation)

        new_organisation.save()
        new_user.save()

        url = '/users/login/'
        data = {'email': 'trinity@bsg.com'}
        response = self.client.get(url, data, format=json)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = {'email': 'emily@bsg.com'}
        response = self.client.get(url, data, format=json)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response_data = json.loads(response.content)["errors"]
        self.assertEqual(response_data, "Can't find user")

