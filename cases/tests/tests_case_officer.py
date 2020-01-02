from django.urls import reverse
from rest_framework import status

from teams.helpers import get_team_by_pk
from test_helpers.clients import DataTestClient


class CaseGetTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application(self.organisation)
        self.case = self.submit_application(self.standard_application)
        team = get_team_by_pk("00000000-0000-0000-0000-000000000001")
        self.user = self.create_gov_user("new_user@their.email.com", team)

    def test_assign_gov_user(self):
        self.url = reverse("cases:case_officer", kwargs={"pk": self.case.id, "govpk": self.user.id})

        self.assertIsNone(self.case.case_officer)

        request = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(request.status_code, status.HTTP_204_NO_CONTENT)
        self.case.refresh_from_db()

        self.assertIsNotNone(self.case.case_officer)

    def test_unassign_gov_user(self):
        self.case.case_officer = self.user
        self.case.save()
        self.url = reverse("cases:case_officers", kwargs={"pk": self.case.id})

        self.assertIsNotNone(self.case.case_officer)

        request = self.client.post(self.url, **self.gov_headers)

        self.assertEqual(request.status_code, status.HTTP_204_NO_CONTENT)

        self.case.refresh_from_db()

        self.assertIsNone(self.case.case_officer)

    def test_get_case_officer(self):
        self.case.case_officer = self.user
        self.case.save()
        self.url = reverse("cases:case_officers", kwargs={"pk": self.case.id})

        request = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(request.status_code, status.HTTP_200_OK)
