from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN
from parameterized import parameterized

from applications.models import BaseApplication
from test_helpers.clients import DataTestClient


class DeleteApplication(DataTestClient):
    def setUp(self):
        super().setUp()
        self.applications = {
            "STANDARD": self.create_standard_application(self.organisation),
            "HMRC": self.create_hmrc_query(self.organisation),
            "EXHIBITION": self.create_exhibition_clearance_application(self.organisation),
        }
        self.users = {"EXPORTER": self.exporter_headers, "GOV": self.gov_headers, "HMRC": self.hmrc_exporter_headers}

    @parameterized.expand([("STANDARD", "EXPORTER"), ("EXHIBITION", "EXPORTER"), ("HMRC", "HMRC")])
    def test_delete_draft_application_as_valid_user_success(self, application_type, user):
        draft = self.applications[application_type]
        headers = self.users[user]
        number_of_applications = BaseApplication.objects.all().count()
        url = reverse("applications:application", kwargs={"pk": draft.id})

        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(number_of_applications - 1, BaseApplication.objects.all().count())

    @parameterized.expand([("STANDARD", "GOV"), ("EXHIBITION", "GOV"), ("HMRC", "EXPORTER")])
    def test_delete_draft_application_as_invalid_user_failure(self, application_type, user):
        draft = self.applications[application_type]
        headers = self.users[user]
        number_of_applications = BaseApplication.objects.all().count()
        url = reverse("applications:application", kwargs={"pk": draft.id})

        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)
        self.assertEqual(number_of_applications, BaseApplication.objects.all().count())

    @parameterized.expand([("STANDARD", "EXPORTER"), ("EXHIBITION", "EXPORTER"), ("HMRC", "HMRC")])
    def test_delete_submitted_application_failure(self, application_type, user):
        draft = self.applications[application_type]
        headers = self.users[user]
        self.submit_application(draft)
        number_of_applications = BaseApplication.objects.all().count()
        url = reverse("applications:application", kwargs={"pk": draft.id})

        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(number_of_applications, BaseApplication.objects.all().count())
