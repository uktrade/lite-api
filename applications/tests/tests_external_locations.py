from django.urls import reverse
from rest_framework import status

from applications.models import SiteOnApplication, ExternalLocationOnApplication
from test_helpers.clients import DataTestClient


class ExternalLocationsOnApplicationTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.application = self.create_standard_application(self.organisation)
        self.external_location = self.create_external_location('storage facility', self.organisation)
        self.url = reverse('applications:application_external_locations', kwargs={'pk': self.application.id})

    def test_add_external_location_to_an_unsubmitted_application(self):
        SiteOnApplication.objects.filter(application=self.application).delete()
        data = {
            'external_locations': [
                self.external_location.id
            ]
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        self.application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExternalLocationOnApplication.objects.filter(application=self.application).count(), 1)
        self.assertEqual(self.application.activity, 'Brokering')

    def test_adding_external_location_to_unsubmitted_application_removes_sites(self):
        data = {
            'external_locations': [
                self.external_location.id
            ]
        }
        self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(SiteOnApplication.objects.filter(application=self.application).count(), 0)
        self.assertEqual(ExternalLocationOnApplication.objects.filter(application=self.application).count(), 1)

    def test_add_external_location_to_a_submitted_application_success(self):
        SiteOnApplication.objects.filter(application=self.application).delete()
        ExternalLocationOnApplication(application=self.application, external_location=self.external_location).save()
        external_location_to_add = self.create_external_location('storage facility 2', self.organisation)
        data = {
            'external_locations': [
                self.external_location.id,
                external_location_to_add.id,
            ]
        }
        self.submit_application(self.application)

        response = self.client.post(self.url, data, **self.exporter_headers)
        self.application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExternalLocationOnApplication.objects.filter(application=self.application).count(), 2)

    def test_add_external_location_to_a_submitted_application_failure(self):
        """
        Cannot add additional external locations to a submitted application unless the additional external location
        is located in a country that is already on the application
        """
        SiteOnApplication.objects.filter(application=self.application).delete()
        ExternalLocationOnApplication(application=self.application, external_location=self.external_location).save()
        external_location_to_add = self.create_external_location('storage facility 2', self.organisation, 'US')
        data = {
            'external_locations': [
                self.external_location.id,
                external_location_to_add.id,
            ]
        }
        self.submit_application(self.application)

        response = self.client.post(self.url, data, **self.exporter_headers)
        self.application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ExternalLocationOnApplication.objects.filter(application=self.application).count(), 1)

    def test_adding_external_location_to_submitted_application_when_sites_already_on_application_failure(self):
        self.submit_application(self.application)
        data = {
            'external_locations': [
                self.external_location.id
            ]
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(SiteOnApplication.objects.filter(application=self.application).count(), 1)
        self.assertEqual(ExternalLocationOnApplication.objects.filter(application=self.application).count(), 0)

    def test_adding_no_external_locations_to_application_failure(self):
        data = {'external_locations': []}

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_removing_external_locations_success(self):
        url = reverse('applications:application_remove_external_location',
                      kwargs={'pk': self.application.id, 'ext_loc_pk': self.external_location.id})

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_removing_external_locations_failure(self):
        ExternalLocationOnApplication(application=self.application, external_location=self.external_location).save()
        self.submit_application(self.application)
        url = reverse('applications:application_remove_external_location',
                      kwargs={'pk': self.application.id, 'ext_loc_pk': self.external_location.id})

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)