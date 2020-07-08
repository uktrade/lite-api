from datetime import timedelta

from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from django.conf import settings
from static.statuses.enums import CaseStatusEnum
from test_helpers.clients import DataTestClient


@override_settings(RECENTLY_UPDATED_WORKING_DAYS=5)
class TestIsRecentlyUpdated(DataTestClient):

    url = reverse("cases:search")
    # Assume 10 + RECENTLY_UPDATED_WORKING_DAYS will contain 5 working days
    past_date = timezone.now() - timedelta(days=settings.RECENTLY_UPDATED_WORKING_DAYS + 10)

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

    def test_recently_submitted_cases_are_flagged_as_updated(self):
        self.create_standard_application_case(self.organisation)

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()["results"]["cases"][0]

        self.assertEqual(response_data["is_recently_updated"], True)
