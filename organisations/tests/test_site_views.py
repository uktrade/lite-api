import json

from django.urls import path, include
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase

from organisations.models import Site
from test_helpers.org_and_user_helper import OrgAndUserHelper


class SiteViewTests(APITestCase, URLPatternsTestCase):

    urlpatterns = [
        path('organisations/', include('organisations.urls'))
    ]

    client = APIClient

    def setUp(self):
        self.test_helper = OrgAndUserHelper(name='Org1')
        self.headers = {'HTTP_USER_ID': str(self.test_helper.user.id)}

    def test_site_list(self):

        url = reverse('organisations:sites')
        response = self.client.get(url, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['sites'][0]['name'], 'headquarters')

    # def test_site_update(self):
    #
    #     url = reverse('organisations:site', kwargs={'org_pk': self.test_helper.organisation.id,
    #                                                 'site_pk': self.test_helper.organisation.primary_site.id})
    #     data = {'name': 'regional site'}
    #
    #     response = self.client.put(url, data, format='json', **self.headers)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     # more tests desirable
    #
    # def test_add_site(self):
    #
    #     url = reverse('organisations:sites', kwargs={'org_pk': self.test_helper.organisation.id})
    #     data = {'name': 'regional site',
    #             'address_line_1': 'a street',
    #             'city': 'london',
    #             'zip': 'E14GH',
    #             'state': 'Hertfordshire',
    #             'country': 'England'}
    #
    #     response = self.client.post(url, data, format='json', **self.headers)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(Site.objects.all().count(), 2)
