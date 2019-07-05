from django.urls import reverse
from rest_framework import status

from static.countries.models import Country
from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper


class CountriesOnDraftTests(DataTestClient):

    COUNTRIES_COUNT = 10

    def setUp(self):
        super().setUp()
        self.org = self.test_helper.organisation
        self.primary_site = self.org.primary_site
        self.draft = OrgAndUserHelper.complete_draft('Goods test', self.org)

        self.url = reverse('drafts:countries', kwargs={'pk': self.draft.id})

    def test_add_countries_to_a_draft_success(self):
        data = {
            'countries': Country.objects.all()[:self.COUNTRIES_COUNT].values_list('id', flat=True)
        }

        response = self.client.post(self.url, data, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(self.url, **self.headers).json()
        self.assertEqual(len(response['countries']), self.COUNTRIES_COUNT)

    def test_add_countries_to_a_draft_failure(self):
        """
        Incorrect values
        """
        data = {
            'countries': ['1234']
        }

        response = self.client.post(self.url, data, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.get(self.url, **self.headers).json()
        self.assertEqual(len(response['countries']), 0)

    def test_add_countries_to_another_orgs_draft_failure(self):
        """
        Ensure that a user cannot add countries to another organisation's draft
        """
        org2 = OrgAndUserHelper(name='organisation2')
        self.draft = OrgAndUserHelper.complete_draft('Goods test', org2.organisation)
        self.url = reverse('drafts:countries', kwargs={'pk': self.draft.id})

        data = {
            'countries': Country.objects.all()[:self.COUNTRIES_COUNT].values_list('id', flat=True)
        }

        response = self.client.post(self.url, data, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.get(self.url, **self.headers).json()
        self.assertEqual(len(response['countries']), 0)
