from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN

from api.applications.models import BaseApplication
from lite_content.lite_api import strings
from test_helpers.clients import DataTestClient


class DeleteApplication(DataTestClient):
    def setUp(self):
        super().setUp()
        self.application = self.create_draft_standard_application(self.organisation)

    def test_delete_draft_application_as_valid_user_success(self):
        """
        Tests that applications can be deleted by their owners when in a draft state
        """
        number_of_applications = BaseApplication.objects.all().count()
        url = reverse("applications:application", kwargs={"pk": self.application.id})

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json()["status"], strings.Applications.Generic.DELETE_DRAFT_APPLICATION)
        self.assertEqual(number_of_applications - 1, BaseApplication.objects.all().count())
        self.assertNotIn(self.application, BaseApplication.objects.all())

    def test_delete_draft_application_as_invalid_user_failure(self):
        """
        Tests that applications cannot be deleted by users who do not own the application
        """
        number_of_applications = BaseApplication.objects.all().count()
        url = reverse("applications:application", kwargs={"pk": self.application.id})

        response = self.client.delete(url, **self.gov_headers)

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)
        self.assertEqual(number_of_applications, BaseApplication.objects.all().count())

    def test_delete_submitted_application_failure(self):
        """
        Tests that applications cannot be deleted after they have been submitted
        """
        self.submit_application(self.application)
        number_of_applications = BaseApplication.objects.all().count()
        url = reverse("applications:application", kwargs={"pk": self.application.id})

        response = self.client.delete(url, **self.exporter_headers)

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"], strings.Applications.Generic.DELETE_SUBMITTED_APPLICATION_ERROR)
        self.assertEqual(number_of_applications, BaseApplication.objects.all().count())
