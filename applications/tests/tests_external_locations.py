from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from applications.libraries.case_status_helpers import get_case_statuses
from applications.models import SiteOnApplication, ExternalLocationOnApplication
from static.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class ExternalLocationsOnApplicationTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.application = self.create_standard_application(self.organisation)
        self.external_location = self.create_external_location("storage facility", self.organisation)
        self.url = reverse("applications:application_external_locations", kwargs={"pk": self.application.id},)

    def test_add_external_location_to_an_unsubmitted_application(self):
        SiteOnApplication.objects.filter(application=self.application).delete()
        data = {"external_locations": [self.external_location.id]}

        response = self.client.post(self.url, data, **self.exporter_headers)
        self.application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            ExternalLocationOnApplication.objects.filter(application=self.application).count(), 1,
        )
        self.assertEqual(self.application.activity, "Brokering")

    def test_adding_external_location_to_unsubmitted_application_removes_sites(self):
        data = {"external_locations": [self.external_location.id]}
        self.client.post(self.url, data, **self.exporter_headers)
        self.assertEqual(SiteOnApplication.objects.filter(application=self.application).count(), 0)
        self.assertEqual(
            ExternalLocationOnApplication.objects.filter(application=self.application).count(), 1,
        )

    def test_add_external_location_to_a_submitted_application_success(self):
        SiteOnApplication.objects.filter(application=self.application).delete()
        ExternalLocationOnApplication(application=self.application, external_location=self.external_location).save()
        external_location_to_add = self.create_external_location("storage facility 2", self.organisation)
        data = {"external_locations": [self.external_location.id, external_location_to_add.id,]}
        self.submit_application(self.application)

        response = self.client.post(self.url, data, **self.exporter_headers)
        self.application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            ExternalLocationOnApplication.objects.filter(application=self.application).count(), 2,
        )

    def test_add_external_location_to_a_submitted_application_failure(self):
        """
        Cannot add additional external locations to a submitted application unless the additional external location
        is located in a country that is already on the application
        """
        SiteOnApplication.objects.filter(application=self.application).delete()
        ExternalLocationOnApplication(application=self.application, external_location=self.external_location).save()
        external_location_to_add = self.create_external_location("storage facility 2", self.organisation, "US")
        data = {"external_locations": [self.external_location.id, external_location_to_add.id,]}
        self.submit_application(self.application)

        response = self.client.post(self.url, data, **self.exporter_headers)
        self.application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            ExternalLocationOnApplication.objects.filter(application=self.application).count(), 1,
        )

    def test_adding_external_location_to_submitted_application_when_sites_already_on_application_failure(self,):
        self.submit_application(self.application)
        data = {"external_locations": [self.external_location.id]}

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(SiteOnApplication.objects.filter(application=self.application).count(), 1)
        self.assertEqual(
            ExternalLocationOnApplication.objects.filter(application=self.application).count(), 0,
        )

    def test_adding_no_external_locations_to_application_failure(self):
        data = {"external_locations": []}

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_removing_external_locations_success(self):
        url = reverse(
            "applications:application_remove_external_location",
            kwargs={"pk": self.application.id, "ext_loc_pk": self.external_location.id},
        )

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_removing_external_locations_failure(self):
        """ Test failure in removing an external location on a submitted, editable application that only has 1 external
        location added.
        """
        ExternalLocationOnApplication(application=self.application, external_location=self.external_location).save()
        self.submit_application(self.application)
        url = reverse(
            "applications:application_remove_external_location",
            kwargs={"pk": self.application.id, "ext_loc_pk": self.external_location.id},
        )

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @parameterized.expand(get_case_statuses(read_only=True))
    def test_remove_external_locations_from_application_in_read_only_status_failure(self, read_only_status):
        ExternalLocationOnApplication(application=self.application, external_location=self.external_location).save()
        url = reverse(
            "applications:application_remove_external_location",
            kwargs={"pk": self.application.id, "ext_loc_pk": self.external_location.id},
        )

        self.application.status = get_case_status_by_status(read_only_status)
        self.application.save()

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.application.external_application_sites.count(), 1)

    @parameterized.expand(get_case_statuses(read_only=False))
    def test_remove_external_locations_from_application_in_editable_status_success(self, editable_status):
        """ Test success in removing an external location from an application in an editable status that has
        more than one external location added.
        """
        application = self.create_standard_application(self.organisation)
        application.status = get_case_status_by_status(editable_status)
        application.save()

        ExternalLocationOnApplication(application=application, external_location=self.external_location).save()
        second_external_location = self.create_external_location("storage facility", self.organisation)
        ExternalLocationOnApplication(application=application, external_location=second_external_location).save()

        url = reverse(
            "applications:application_remove_external_location",
            kwargs={"pk": application.id, "ext_loc_pk": self.external_location.id},
        )

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(application.external_application_sites.count(), 1)

    @parameterized.expand(get_case_statuses(read_only=False))
    def test_add_external_locations_to_application_in_editable_status_success(self, editable_status):
        data = {"external_locations": [self.external_location.id]}

        application = self.create_standard_application(self.organisation)
        application.status = get_case_status_by_status(editable_status)
        application.save()
        SiteOnApplication.objects.filter(application=application).delete()

        url = reverse("applications:application_external_locations", kwargs={"pk": application.id})
        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(application.external_application_sites.count(), 1)

    @parameterized.expand(get_case_statuses(read_only=True))
    def test_add_external_locations_to_application_in_read_only_status_failure(self, read_only_status):
        data = {"external_locations": [self.external_location.id]}

        application = self.create_standard_application(self.organisation)
        application.status = get_case_status_by_status(read_only_status)
        application.save()

        url = reverse("applications:application_external_locations", kwargs={"pk": application.id})
        response = self.client.post(url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(application.external_application_sites.count(), 0)
