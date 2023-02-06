import pytest
from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient
from django.core.exceptions import ValidationError


class CasesUpdateCaseOfficerTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_draft_standard_application(self.organisation)
        self.user = self.create_gov_user("new_user@their.email.com", self.team)  # /PS-IGNORE
        self.url = reverse("cases:cases_update_case_officer")

    def test_assign_gov_user_to_multiple_cases(self):
        case_1 = self.submit_application(self.standard_application)
        case_2 = self.submit_application(self.standard_application)

        request = self.client.put(
            self.url, data={"gov_user_pk": self.user.pk, "case_ids": [case_1.pk, case_2.pk]}, **self.gov_headers
        )

        self.assertEqual(request.status_code, status.HTTP_200_OK)
        case_1.refresh_from_db()
        case_2.refresh_from_db()
        self.assertIsNotNone(case_1.case_officer)
        self.assertIsNotNone(case_2.case_officer)

    def test_assign_gov_user_to_multiple_cases_bad_request(self):

        request = self.client.put(self.url, data={"gov_user_pk": self.user.pk}, **self.gov_headers)

        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)

    def test_assign_gov_user_to_multiple_cases_invalid(self):
        with pytest.raises(ValidationError):
            self.client.put(self.url, data={"gov_user_pk": self.user.pk, "case_ids": ["ambmsb@"]}, **self.gov_headers)
