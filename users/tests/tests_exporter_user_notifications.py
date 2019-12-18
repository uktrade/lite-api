from django.contrib.contenttypes.models import ContentType
from django.urls import reverse_lazy
from rest_framework import status

from users.models import ExporterNotification
from test_helpers.clients import DataTestClient
from users.libraries.user_to_token import user_to_token


class NotificationTests(DataTestClient):
    def _create_clc_query_with_notifications(self):
        clc_query = self.create_clc_query(description="this is a clc query", organisation=self.organisation)
        self.create_case_note(clc_query, "This is a test note 1", self.gov_user, True)
        self.create_ecju_query(clc_query, "This is an ecju query")
        self.create_generated_case_document(clc_query, template=self.create_letter_template())
        return clc_query

    def _create_application_with_notifications(self):
        application = self.create_standard_application_case(self.organisation)
        self.create_case_note(application, "This is a test note 1", self.gov_user, True)
        self.create_ecju_query(application, "This is an ecju query")
        self.create_generated_case_document(application, template=self.create_letter_template())
        return application

    def _create_end_user_advisory_query_with_notifications(self):
        eua_query = self.create_end_user_advisory_case("note", "reasoning", self.organisation)
        self.create_case_note(eua_query, "This is a test note 1", self.gov_user, True)
        self.create_ecju_query(eua_query, "This is an ecju query")
        self.create_generated_case_document(eua_query, template=self.create_letter_template())
        return eua_query

    def _create_hmrc_query_with_notifications(self):
        hmrc_query = self.create_hmrc_query(self.organisation)
        self.create_case_note(hmrc_query, "This is a test note 1", self.gov_user, True)
        self.create_ecju_query(hmrc_query, "This is an ecju query")
        self.create_generated_case_document(hmrc_query, template=self.create_letter_template())
        return hmrc_query

    def tests_create_new_clc_query_notifications_success(self):
        clc_query = self._create_clc_query_with_notifications()
        self.create_case_note(clc_query, "This is a test note 4", self.gov_user, False)

        self.assertEqual(
            ExporterNotification.objects.filter(
                user=self.exporter_user, organisation=self.exporter_user.organisation, case=clc_query,
            ).count(),
            3,
        )

    def test_create_new_application_notifications_success(self):
        application = self._create_application_with_notifications()
        self.create_case_note(application, "This is a test note 2", self.gov_user, False)

        self.assertEqual(
            ExporterNotification.objects.filter(
                user=self.exporter_user, organisation=self.exporter_user.organisation, case=application,
            ).count(),
            3,
        )

    def test_create_new_eua_query_notifications_success(self):
        eua_query = self._create_end_user_advisory_query_with_notifications()
        self.create_case_note(eua_query, "This is a test note 2", self.gov_user, False)

        self.assertEqual(
            ExporterNotification.objects.filter(
                user=self.exporter_user, organisation=self.exporter_user.organisation, case=eua_query,
            ).count(),
            3,
        )

    def test_create_new_hmrc_query_notifications_success(self):
        hmrc_query = self._create_hmrc_query_with_notifications()
        self.create_case_note(hmrc_query, "This is a test note 2", self.gov_user, False)

        self.assertEqual(
            ExporterNotification.objects.filter(
                user=self.exporter_user, organisation=self.exporter_user.organisation, case=hmrc_query,
            ).count(),
            3,
        )

    def tests_get_notifications_for_user_success(self):
        self._create_end_user_advisory_query_with_notifications()
        self._create_hmrc_query_with_notifications()
        self._create_application_with_notifications()
        self._create_clc_query_with_notifications()

        response = self.client.get(reverse_lazy("users:notifications"), **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("notifications", response_data)
        self.assertIn("notifications_count", response_data)
        self.assertEqual(len(response_data["notifications"]), 12)
        self.assertEqual(response_data["notifications_count"]["application"], 3)
        self.assertEqual(response_data["notifications_count"]["end_user_advisory_query"], 3)
        self.assertEqual(response_data["notifications_count"]["hmrc_query"], 3)
        self.assertEqual(response_data["notifications_count"]["clc_query"], 3)

    def tests_get_notifications_for_user_count_only_success(self):
        self._create_end_user_advisory_query_with_notifications()
        self._create_hmrc_query_with_notifications()
        self._create_application_with_notifications()
        self._create_clc_query_with_notifications()

        response = self.client.get(reverse_lazy("users:notifications") + "?count_only=True", **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("notifications", response_data)
        self.assertIn("notifications_count", response_data)
        self.assertEqual(response_data["notifications_count"]["application"], 3)
        self.assertEqual(response_data["notifications_count"]["end_user_advisory_query"], 3)
        self.assertEqual(response_data["notifications_count"]["hmrc_query"], 3)
        self.assertEqual(response_data["notifications_count"]["clc_query"], 3)

    def tests_get_notifications_for_user_in_multiple_orgs_success(self):
        """
        Given an exporter user in multiple orgs
        When an API user gets notifications for the exporter user and one of their orgs
        Then the notifications specific to that user and org combination are returned
        """
        url = reverse_lazy("users:notifications")
        application1 = self.create_standard_application_case(self.organisation)
        self.create_case_note(application1, "This is a test note 1", self.gov_user, True)
        self.create_case_note(application1, "This is a test note 2", self.gov_user, True)

        org_2, _ = self.create_organisation_with_exporter_user("Org 2")
        self.add_exporter_user_to_org(org_2, self.exporter_user)
        self.exporter_headers = {
            "HTTP_EXPORTER_USER_TOKEN": user_to_token(self.exporter_user),
            "HTTP_ORGANISATION_ID": org_2.id,
        }
        application2 = self.create_standard_application_case(org_2)
        case_note1 = self.create_case_note(application2, "This is a test note 3", self.gov_user, True)
        case_note2 = self.create_case_note(application2, "This is a test note 4", self.gov_user, True)
        case_notes = [str(case_note1.id), str(case_note2.id)]

        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data["notifications"]), 2)
        # Check that the 2 notifications we got are the ones arising from notes on application 2, i.e. the application
        # created while org_2 is the currently selected org
        for data in response_data["notifications"]:
            self.assertTrue(data["object_id"] in case_notes)
        self.assertEqual(response_data["notifications_count"]["application"], 2)
