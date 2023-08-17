from rest_framework import status

from django.urls import reverse

from test_helpers.clients import DataTestClient


class AppealApplicationTests(DataTestClient):
    def test_appeal_standard_application(self):
        application = self.create_standard_application_case(self.organisation)

        self.assertIsNone(application.appeal)

        url = reverse(
            "applications:appeal",
            kwargs={"pk": application.id},
        )
        response = self.client.post(
            url,
            {"grounds_for_appeal": "These are the grounds for appeal"},
            **self.exporter_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        application.refresh_from_db()
        self.assertIsNotNone(application.appeal)
        self.assertEqual(
            application.appeal.grounds_for_appeal,
            "These are the grounds for appeal",
        )
        self.assertEqual(
            response.json(),
            {"grounds_for_appeal": "These are the grounds for appeal"},
        )

    def test_appeal_invalid_application_pk(self):
        url = reverse(
            "applications:appeal",
            kwargs={"pk": "4ec19e01-71ec-40fc-83c1-442c2706868d"},
        )
        response = self.client.post(
            url,
            {"grounds_for_appeal": "These are the grounds for appeal"},
            **self.exporter_headers,
        )
        self.assertEqual(response.status_code, 404)
