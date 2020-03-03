from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from static.statuses.enums import CaseStatusEnum
from test_helpers.clients import DataTestClient


class TestIsRecentlyUpdated(DataTestClient):

    url = reverse("cases:search")
    past_date = timezone.now() - timedelta(days=10)

    def test_not_recently_updated(self):
        case = self.create_standard_application_case(self.organisation)
        case.submitted_at = self.past_date
        case.save()

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()["results"]["cases"][0]

        self.assertEqual(response_data["is_recently_updated"], False)

    def test_recently_updated(self):
        case = self.create_standard_application_case(self.organisation)
        case.submitted_at = self.past_date
        case.save()

        # GOV user updates the case (changes the status of it)
        data = {"status": CaseStatusEnum.RESUBMITTED}
        self.client.put(reverse("applications:manage_status", kwargs={"pk": case.id}), data=data, **self.gov_headers)

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()["results"]["cases"][0]

        self.assertEqual(response_data["is_recently_updated"], True)

    def test_exporter_user_cannot_trigger_recently_updated(self):
        case = self.create_standard_application_case(self.organisation)
        case.submitted_at = self.past_date
        case.save()

        # Exporter user updates the case (changes the status of it)
        data = {"status": CaseStatusEnum.APPLICANT_EDITING}
        self.client.put(
            reverse("applications:manage_status", kwargs={"pk": case.id}), data=data, **self.exporter_headers
        )

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()["results"]["cases"][0]

        self.assertEqual(response_data["is_recently_updated"], False)

    def test_recently_updated_if_case_is_younger_than_five_days(self):
        self.create_standard_application_case(self.organisation)

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()["results"]["cases"][0]

        self.assertEqual(response_data["is_recently_updated"], True)
