from rest_framework import status
from rest_framework.reverse import reverse

from test_helpers.clients import BaseTestClient


class UnitsTests(BaseTestClient):

    url = reverse('static:units:units')

    def test_get_units(self):
        response = self.client.get(self.url)
        units = response.json()['units']

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(units['NAR'], 'Number of articles')
