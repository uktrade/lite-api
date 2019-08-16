from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper
from users.models import ExporterUser, UserOrganisationRelationship, Organisation


class UserTests(DataTestClient):

    def test_user_creates_new_user(self):
        email = 'jsmith@name.com'
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': email,
            'password': 'password123'
        }
        url = reverse('users:users')
        response = self.client.post(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExporterUser.objects.filter(organisation=self.test_helper.organisation).count(), 2)

        organisation = Organisation.objects.create(
            name='test-org',
            eori_number='123',
            sic_number='',
            vat_number='',
            registration_number='',

        )

        # where they are in a different organisation
        data['organisation'] = str(organisation.id)

        url = reverse('users:users')
        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user_org_count = UserOrganisationRelationship.objects.filter(
            user__email=email
        ).count()

        self.assertEqual(user_org_count, 2)

    def test_fail_not_add_multiple_same_user_organisation(self):
        organisation = Organisation.objects.create(
            name='test-org',
            eori_number='123',
            sic_number='',
            vat_number='',
            registration_number='',
        )
        email = 'jsmith@name.com'
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': email,
            'password': 'password123',
            'organisation': str(organisation.id)
        }
        url = reverse('users:users')
        response = self.client.post(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, 201)
        user_org_count = UserOrganisationRelationship.objects.filter(
            user__email=email
        ).count()
        self.assertEqual(user_org_count, 1)
        response = self.client.post(url, data, **self.exporter_headers)
        # check status code for correct user behaviour
        self.assertEqual(response.status_code, 201)
        user_org_count = UserOrganisationRelationship.objects.filter(
            user__email=email
        ).count()
        self.assertEqual(user_org_count, 1)

    def test_fail_create_new_user(self):
        data = {}
        url = reverse('users:users')
        response = self.client.post(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ExporterUser.objects.filter(organisation=self.test_helper.organisation).count(), 1)
