from rest_framework import status
from rest_framework.reverse import reverse

from addresses.models import Address
from organisations.models import Site
from test_helpers.clients import DataTestClient


class SiteViewTests(DataTestClient):
    
    url = reverse('organisations:sites')

    def test_site_list(self):
        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data['sites']), 1)

    def test_site_name_update(self):
        url = reverse('organisations:site', kwargs={'pk': self.exporter_user.organisation.primary_site.id})

        data = {
            'name': 'regional site',
            'address': {},
        }

        pk = self.organisation.primary_site.id
        response = self.client.put(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Site.objects.get(pk=pk).name, 'regional site')

    def test_edit_address_and_name_of_site(self):
        url = reverse('organisations:site', kwargs={'pk': self.exporter_user.organisation.primary_site.id})
        data = {
            'name': 'regional site',
            'address': {
                'address_line_1': '43 Commercial Road',
                'address_line_2': 'The place'
            },
        }

        site_id = self.organisation.primary_site.id
        response = self.client.put(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Site.objects.get(id=site_id).name, data['name'])
        self.assertEqual(Site.objects.get(id=site_id).address.address_line_1, data['address']['address_line_1'])
        self.assertEqual(Site.objects.get(id=site_id).address.address_line_2, data['address']['address_line_2'])

    def test_add_site(self):
        url = reverse('organisations:sites')
        data = {
            'name': 'regional site',
            'address': {
                'address_line_1': 'a street',
                'city': 'london',
                'postcode': 'E14GH',
                'region': 'Hertfordshire',
                'country': 'GB'},
        }

        response = self.client.post(url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Site.objects.all().count(), 2)

    def test_add_site_via_helper(self):
        self.create_site('org2', self.exporter_user.organisation)
        self.assertEqual(Site.objects.all().count(), 2)
        # There is a dummy address which means there are two real ones after
        # the create additional site and the one dummy one.
        self.assertEqual(Address.objects.all().count(), 2)


class OrgSiteViewTests(DataTestClient):

    def test_site_list(self):
        url = reverse('organisations:organisation_sites', kwargs={'org_pk': self.exporter_user.organisation.id})

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data['sites']), 1)

    def test_add_site(self):
        url = reverse('organisations:organisation_sites', kwargs={'org_pk': self.exporter_user.organisation.id})
        data = {
            'name': 'regional site',
            'address': {
                'address_line_1': 'a street',
                'city': 'london',
                'postcode': 'E14GH',
                'region': 'Hertfordshire',
                'country': 'GB'},
        }

        response = self.client.post(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Site.objects.all().count(), 2)
        self.assertEqual(Site.objects.filter(organisation=self.exporter_user.organisation).count(), 2)

    def test_edit_address_and_name_of_site(self):
        url = reverse('organisations:organisation_site',
                      kwargs={'org_pk': self.exporter_user.organisation.id,
                              'site_pk': self.exporter_user.organisation.primary_site.id})
        data = {'name': 'regional site',
                'address': {
                    'address_line_1': '43 Commercial Road',
                    'address_line_2': 'The place'
                },
                }

        id = self.organisation.primary_site.id
        response = self.client.put(url, data, **self.gov_headers)
        self.assertEqual(Site.objects.get(id=id).address.address_line_1, '43 Commercial Road')
        self.assertEqual(Site.objects.get(id=id).address.address_line_2, 'The place')
        self.assertEqual(Site.objects.get(id=id).name, 'regional site')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # The Test below is not expected to work until the Users/Permissions framework
    # is implemented
    # def test_user_can_only_see_their_own_sites(self):
    #     OrgAndUserHelper('org2')
    #     self.assertEqual(Site.objects.all().count(), 2)
    #     url = reverse('organisations:sites', kwargs={'org_pk': self.exporter_user.organisation.id})
    #     response = self.client.get(url, **self.exporter_headers)
    #     response_data = response.json()
    #     self.assertEqual(response_data['sites'][0]['id'], str(self.organisation.primary_site.id))
    #     self.assertEqual(len(response_data['sites']), 1)

    def test_add_site_via_helper(self):
        self.create_site('org2', self.exporter_user.organisation)
        self.assertEqual(Site.objects.all().count(), 2)
        # There is a dummy address which means there are two real ones after
        # the create additional site and the one dummy one.
        self.assertEqual(Address.objects.all().count(), 2)
