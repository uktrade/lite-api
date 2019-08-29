from rest_framework import status
from rest_framework.reverse import reverse

from organisations.models import Site
from static.countries.helpers import get_country
from test_helpers.clients import DataTestClient


class OrganisationSitesTests(DataTestClient):

    def test_site_list(self):
        url = reverse('organisations:sites', kwargs={'org_pk': self.organisation.id})

        # Create an additional organisation and site to ensure
        # that only sites from the first organisation are shown
        self.create_organisation('New Org')

        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data['sites']), 1)

    def test_add_site(self):
        url = reverse('organisations:sites', kwargs={'org_pk': self.organisation.id})

        data = {
            'name': 'regional site',
            'address': {
                'address_line_1': 'a street',
                'city': 'london',
                'postcode': 'E14GH',
                'region': 'Hertfordshire',
                'country': 'GB'
            },
        }

        response = self.client.post(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Site.objects.all().count(), 2)
        self.assertEqual(Site.objects.filter(organisation=self.organisation).count(), 2)

    def test_edit_site(self):
        url = reverse('organisations:site',
                      kwargs={'org_pk': self.organisation.id,
                              'site_pk': self.organisation.primary_site.id})

        data = {
            'name': 'regional site',
            'address': {
                'address_line_1': '43 Commercial Road',
                'address_line_2': 'The place',
                'country': 'GB',
            }
        }
        response = self.client.put(url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        site = self.organisation.primary_site
        site.refresh_from_db()

        self.assertEqual(site.name, data['name'])
        self.assertEqual(site.address.address_line_1, data['address']['address_line_1'])
        self.assertEqual(site.address.address_line_2, data['address']['address_line_2'])
        self.assertEqual(site.address.country, get_country(data['address']['country']))
