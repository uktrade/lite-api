from django.urls import reverse
from rest_framework import status

from gov_users.libraries.user_to_token import user_to_token
from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper
from users.models import ExporterUser, Organisation


class UserTests(DataTestClient):

    def test_user_creates_new_user(self):
        email = 'jsmith@name.com'
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': email,
        }
        url = reverse('users:users')
        response = self.client.post(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExporterUser.objects.filter(organisation=self.exporter_user.organisation).count(), 2)

        test_helper_2 = OrgAndUserHelper('org2')
        exporter_2_headers = {'HTTP_EXPORTER_USER_TOKEN': user_to_token(test_helper_2.user)}

        url = reverse('users:users')
        response = self.client.post(url, data, **exporter_2_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user_org_count = ExporterUser.objects.filter(
            email=email
        ).count()

        self.assertEqual(user_org_count, 2)
    #
    def test_fail_not_add_multiple_same_user_organisation(self):
        email = 'jsmith@name.com'
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': email,
        }
        url = reverse('users:users')
        response = self.client.post(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, 201)

        response = self.client.post(url, data, **self.exporter_headers)
        # check status code for correct user behaviour
        self.assertEqual(response.status_code, 400)

    def test_fail_create_new_user(self):
        data = {}
        url = reverse('users:users')
        response = self.client.post(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ExporterUser.objects.filter(organisation=self.exporter_user.organisation).count(), 1)
