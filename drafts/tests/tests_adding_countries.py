from django.urls import reverse
from rest_framework import status

from drafts.models import Draft
from static.countries.models import Country
from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper


class CountriesOnDraftTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.org = self.test_helper.organisation
        self.primary_site = self.org.primary_site
        self.draft = OrgAndUserHelper.complete_draft('Goods test', self.org)

        self.url = reverse('drafts:countries', kwargs={'pk': self.draft.id})

    def test_add_countries_to_a_draft_success(self):
        countries_count = 10

        data = {
            'countries': Country.objects.all()[:countries_count].values_list('id', flat=True)
        }

        response = self.client.post(self.url, data, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.draft = Draft.objects.get(pk=self.draft.id)

        response = self.client.get(self.url, **self.headers).json()
        self.assertEqual(len(response['countries']), countries_count)