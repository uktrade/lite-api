import json

from rest_framework import status
from rest_framework.test import APITestCase, URLPatternsTestCase, APIClient, force_authenticate

from organisations.models import Organisation
from users.models import User
from django.urls import path, include


class TestHelper:
    @staticmethod
    def create_user_and_organisation():
        new_organisation = Organisation(name='Banana Stand ltd',
                                        eori_number='GB123456789000',
                                        sic_number='2765',
                                        vat_number='123456789',
                                        registration_number='987654321',
                                        address='London')

        new_user = User(email='trinity@bsg.com',
                        username='trinity@bsg.com',
                        organisation=new_organisation)
        new_user.set_password('password')

        new_organisation.save()
        new_user.save()

        return new_user, new_organisation


class UserTests(APITestCase, URLPatternsTestCase):

    urlpatterns = [
        path('users/', include('users.urls')),
    ]

    client = APIClient()

    def test_user_model(self):
        new_user, new_organisation = TestHelper.create_user_and_organisation()

        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().email, 'trinity@bsg.com')
        self.assertEqual(User.objects.get().organisation, new_organisation)

    def test_get_signed_in_user(self):
        TestHelper.create_user_and_organisation()

        url = '/users/me/'

        user = User.objects.get(username='trinity@bsg.com')
        self.client.force_authenticate(user=user, token=user.auth_token)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
