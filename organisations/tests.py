from django.test import TestCase, Client
from rest_framework import status
from organisations.models import Organisation
from users.models import User


class OrganisationTests(TestCase):

    def test_create_organisation_with_first_user(self):

        name="Big Scary Guns ltd"
        eori_number="GB123456789000"
        sic_number="2765"
        address="London"
        admin_user_email="trinity@bsg.com"

        url = '/organisations/'
        data = {'name': name, 'eori_number': eori_number, 'sic_number': sic_number, 'address': address, 'admin_user_email': admin_user_email}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Organisation.objects.get().name, "Big Scary Guns ltd")
        self.assertEqual(Organisation.objects.get().eori_number, "GB123456789000")
        self.assertEqual(Organisation.objects.get().sic_number, "2765")
        self.assertEqual(Organisation.objects.get().address, "London")
        self.assertEqual(User.objects.get().email, "trinity@bsg.com")
