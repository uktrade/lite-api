import json

from django.urls import path, include
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase

from addresses.models import Address
from organisations.models import Site
from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper


class OrgEndUserViewTests(DataTestClient):

    urlpatterns = [
        path('organisations/', include('organisations.urls'))
    ]

    client = APIClient

    # def setUp(self):
    #     self.test_helper = OrgAndUserHelper(name='Org1')
    #     self.headers = {'HTTP_USER_ID': str(self.test_helper.user.id)}
    #     self.end_user = OrgAndUserHelper.create_end_user('test', self.org)

    def setUp(self):
        super().setUp()
        self.org = self.test_helper.organisation
        self.primary_site = self.org.primary_site
        self.draft = OrgAndUserHelper.complete_draft('Goods test', self.org)
        self.end_user = OrgAndUserHelper.create_end_user('test_user', self.org)

        # self.url = reverse('drafts:end_users', kwargs={'pk': self.draft.id})
        self.url = reverse('organisations:organisation_endusers',
                           kwargs={'org_pk': self.test_helper.organisation.id})

    def test_site_list(self):

        url = reverse('organisations:organisation_endusers', kwargs={'org_pk': self.test_helper.organisation.id})
        response = self.client.get(url, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['end_users'][0]['name'], 'test_user')

    # def test_add_site(self):
    #
    #     url = reverse('organisations:organisation_sites',
    #                   kwargs={'org_pk': self.test_helper.organisation.id})
    #     data = {'name': 'regional site',
    #             'address': {
    #                 'address_line_1': 'a street',
    #                 'city': 'london',
    #                 'postcode': 'E14GH',
    #                 'region': 'Hertfordshire',
    #                 'country': 'England'}, }
    #
    #     response = self.client.post(url, data, format='json', **self.headers)
    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    #     self.assertEqual(Site.objects.all().count(), 2)
    #
    #     self.assertEqual(Site.objects.filter(organisation=self.test_helper.organisation).count(), 2)
    #
    # def test_edit_address_and_name_of_site(self):
    #     url = reverse('organisations:organisation_site',
    #                   kwargs={'org_pk': self.test_helper.organisation.id,
    #                           'site_pk': self.test_helper.organisation.primary_site.id})
    #     data = {'name': 'regional site',
    #             'address': {
    #                 'address_line_1': '43 Commercial Road',
    #                 'address_line_2': 'The place'
    #                 },
    #             }
    #
    #     id = self.test_helper.primary_site.id
    #     response = self.client.put(url, data, format='json', **self.headers)
    #     self.assertEqual(Site.objects.get(id=id).address.address_line_1, '43 Commercial Road')
    #     self.assertEqual(Site.objects.get(id=id).address.address_line_2, 'The place')
    #     self.assertEqual(Site.objects.get(id=id).name, 'regional site')
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #
    # # The Test below is not expected to work until the Users/Permissions framework
    # # is implemented
    # # def test_user_can_only_see_their_own_sites(self):
    # #     OrgAndUserHelper('org2')
    # #     self.assertEqual(Site.objects.all().count(), 2)
    # #     url = reverse('organisations:sites', kwargs={'org_pk': self.test_helper.organisation.id})
    # #     response = self.client.get(url, **self.headers)
    # #     response_data = json.loads(response.content)
    # #     self.assertEqual(response_data['sites'][0]['id'], str(self.test_helper.primary_site.id))
    # #     self.assertEqual(len(response_data['sites']), 1)
    #
    # def test_add_site_via_helper(self):
    #     OrgAndUserHelper.create_site('org2', self.test_helper.organisation)
    #     self.assertEqual(Site.objects.all().count(), 2)
    #     # There is a dummy address which means there are two real ones after
    #     # the create additional site and the one dummy one.
    #     self.assertEqual(Address.objects.all().count(), 3)