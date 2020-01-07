from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient


class CaseOfficerTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application(self.organisation)
        self.case = self.submit_application(self.standard_application)
        self.user = self.create_gov_user("new_user@their.email.com", self.team)
        self.url = reverse("cases:case_officer", kwargs={"pk": self.case.id})

    def test_assign_gov_user(self):
        request = self.client.put(self.url, data={"gov_user_pk": self.user.id}, **self.gov_headers)

        self.assertEqual(request.status_code, status.HTTP_204_NO_CONTENT)
        self.case.refresh_from_db()

        self.assertIsNotNone(self.case.case_officer)

    def test_unassign_gov_user(self):
        self.case.case_officer = self.user
        self.case.save()

        request = self.client.delete(self.url, data={}, **self.gov_headers)

        self.assertEqual(request.status_code, status.HTTP_204_NO_CONTENT)

        self.case.refresh_from_db()

        self.assertIsNone(self.case.case_officer)

    def test_get_case_officer(self):
        self.case.case_officer = self.user
        self.case.save()

        request = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(request.status_code, status.HTTP_200_OK)
