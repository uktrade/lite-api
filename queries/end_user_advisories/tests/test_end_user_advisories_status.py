from django.urls import reverse
from rest_framework import status

from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class EndUserAdvisoryStatus(DataTestClient):
    def setUp(self):
        super().setUp()
        self.query = self.create_end_user_advisory("A note", "Unsure about something", self.organisation)
        self.query.status = get_case_status_by_status(CaseStatusEnum.CLOSED)
        self.query.save()

        self.url = reverse("queries:end_user_advisories:end_user_advisory", kwargs={"pk": self.query.id})

    def test_gov_set_status_when_no_permission_to_reopen_closed_cases_failure(self):
        data = {"status": CaseStatusEnum.SUBMITTED}

        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_gov_set_status_when_they_have_permission_to_reopen_closed_cases_success(self):
        data = {"status": CaseStatusEnum.SUBMITTED}

        # Give gov user super used role, to include reopen closed cases permission
        self.gov_user.role = self.super_user_role
        self.gov_user.save()

        response = self.client.put(self.url, data=data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
