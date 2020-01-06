from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient
from users.enums import UserStatuses


class CaseOfficerTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application(self.organisation)
        self.case = self.submit_application(self.standard_application)
        self.user = self.create_gov_user("new_user@their.email.com", self.team)

    def test_assign_gov_user(self):
        self.url = reverse("cases:case_officer", kwargs={"pk": self.case.id, "gov_user_pk": self.user.id})

        request = self.client.post(self.url, data={}, **self.gov_headers)

        self.assertEqual(request.status_code, status.HTTP_204_NO_CONTENT)
        self.case.refresh_from_db()

        self.assertIsNotNone(self.case.case_officer)

    def test_unassign_gov_user(self):
        self.case.case_officer = self.user
        self.case.save()
        self.url = reverse("cases:case_officers", kwargs={"pk": self.case.id})

        request = self.client.delete(self.url, data={}, **self.gov_headers)

        self.assertEqual(request.status_code, status.HTTP_204_NO_CONTENT)

        self.case.refresh_from_db()

        self.assertIsNone(self.case.case_officer)

    def test_get_case_officer(self):
        self.case.case_officer = self.user
        self.case.save()
        self.url = reverse("cases:case_officers", kwargs={"pk": self.case.id})

        request = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(request.status_code, status.HTTP_200_OK)

    def test_dont_get_deactivated_users(self):
        self.user.status = UserStatuses.DEACTIVATED
        self.user.save()

        self.url = reverse("cases:case_officers", kwargs={"pk": self.case.id})

        request = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(request.status_code, status.HTTP_200_OK)

        response_data = request.json()["GovUsers"]

        for user in response_data["users"]:
            self.assertIsNot(user["id"], self.user.id, "deactivated user should not be returned")
