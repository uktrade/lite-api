from django.urls import reverse
from rest_framework import status

from applications.models import CountryOnApplication
from static.countries.helpers import get_country
from static.countries.models import Country
from test_helpers.clients import DataTestClient


class CountriesOnDraftApplicationTests(DataTestClient):
    COUNTRIES_COUNT = 10

    def setUp(self):
        super().setUp()
        self.draft = self.create_open_application(self.organisation)

        self.url = reverse('applications:countries', kwargs={'pk': self.draft.id})

    def test_add_countries_to_a_draft_success(self):
        data = {
            'countries': Country.objects.all()[:self.COUNTRIES_COUNT].values_list('id', flat=True)
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(self.url, **self.exporter_headers).json()
        self.assertEqual(len(response['countries']), self.COUNTRIES_COUNT)

    def test_add_no_countries_to_a_draft_failure(self):
        data = {'countries': []}

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_countries_to_a_submitted_application_failure(self):
        self.submit_application(self.draft)
        countries_on_app_before = CountryOnApplication.objects.filter(application=self.draft).count()
        data = {
            'countries': Country.objects.all()[:self.COUNTRIES_COUNT].values_list('id', flat=True)
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CountryOnApplication.objects.filter(application=self.draft).count(), countries_on_app_before)

    def test_remove_countries_from_a_submitted_application_success(self):
        CountryOnApplication(application=self.draft, country=get_country('US')).save()
        self.submit_application(self.draft)
        countries_on_app_before = CountryOnApplication.objects.filter(application=self.draft).count()
        data = {'countries': [get_country('GB').pk]}

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CountryOnApplication.objects.filter(application=self.draft).count(),
                         countries_on_app_before - 1)

    def test_add_countries_to_a_draft_standard_application_failure(self):
        std_draft = self.create_standard_application(self.organisation)
        pre_test_country_count = CountryOnApplication.objects.all().count()

        data = {
            'countries': Country.objects.all()[:self.COUNTRIES_COUNT].values_list('id', flat=True)
        }
        url = reverse('applications:countries', kwargs={'pk': std_draft.id})

        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CountryOnApplication.objects.all().count(), pre_test_country_count)

    def test_add_countries_to_a_draft_failure(self):
        """
        Incorrect values
        """
        data = {
            'countries': ['1234']
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.get(self.url, **self.exporter_headers).json()
        self.assertEqual(len(response['countries']), 1)

    def test_add_countries_to_another_orgs_draft_failure(self):
        """
        Ensure that a user cannot add countries to another organisation's draft
        """
        organisation_2, _ = self.create_organisation_with_exporter_user()
        self.draft = self.create_open_application(organisation_2)
        self.url = reverse('applications:countries', kwargs={'pk': self.draft.id})

        data = {
            'countries': Country.objects.all()[:self.COUNTRIES_COUNT].values_list('id', flat=True)
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.get(self.url, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
