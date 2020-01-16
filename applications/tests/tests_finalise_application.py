from django.urls import reverse
from rest_framework import status

from applications.enums import Duration
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class FinaliseApplicationTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application(self.organisation)
        self.submit_application(self.standard_application)
        self.url = reverse("applications:finalise", kwargs={"pk": self.standard_application.id})

    def test_gov_super_user_finalise_application(self):
        self.assertEqual(self.standard_application.duration, None)

        # Give gov user super used role, to include reopen closed cases permission
        self.gov_user.role = self.super_user_role
        self.gov_user.save()

        data = {"duration": 12}
        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.standard_application.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.standard_application.status, get_case_status_by_status(CaseStatusEnum.FINALISED))
        self.assertEqual(self.standard_application.duration, data["duration"])

    def test_invalid_duration_data(self):
        # Give gov user super used role, to include reopen closed cases permission
        self.gov_user.role = self.super_user_role
        self.gov_user.save()

        data = {"duration": Duration.MAX + 1}
        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'errors': {'non_field_errors': ['Duration 1000 not in range [1-999]']}})
