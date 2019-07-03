from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient


class FlagsListTests(DataTestClient):

    url = reverse('flags:flags')

    def test_gov_user_can_see_all_flags(self):
        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_whitelisted_gov_user_cannot_see_the_flags(self):
        headers = {'HTTP_GOV_USER_EMAIL': str('test2@mail.com')}
        response = self.client.get(self.url, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
