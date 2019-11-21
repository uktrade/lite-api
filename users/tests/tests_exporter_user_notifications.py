from django.urls import reverse_lazy
from rest_framework import status

from cases.models import Case, Notification
from test_helpers.clients import DataTestClient
from users.libraries.user_to_token import user_to_token


class NotificationTests(DataTestClient):

    url = reverse_lazy("users:notifications")

    def tests_create_new_clc_query_notification(self):
        clc_case = self.create_clc_query("Example CLC Query", self.organisation)

        self.create_case_note(clc_case, "This is a test note 1", self.gov_user, True)
        self.create_case_note(clc_case, "This is a test note 2", self.gov_user, True)
        self.create_case_note(clc_case, "This is a test note 3", self.gov_user, True)
        self.create_case_note(clc_case, "This is a test note 4", self.gov_user, False)

        self.assertEqual(Notification.objects.all().count(), 3)

    def test_create_new_application_notification(self):
        application = self.create_standard_application(self.organisation)
        self.submit_application(application)
        case = application

        self.create_case_note(case, "This is a test note 1", self.gov_user, True)
        self.create_case_note(case, "This is a test note 2", self.gov_user, False)

        self.assertEqual(Notification.objects.all().count(), 1)

    def test_create_both_clc_and_application_notifications(self):
        application = self.create_standard_application(self.organisation)
        case = self.submit_application(application)

        clc_case = self.create_clc_query("Example CLC Query", self.organisation)

        self.create_case_note(case, "This is a test note 1", self.gov_user, True)
        self.create_case_note(case, "This is a test note 2", self.gov_user, True)
        self.create_case_note(case, "This is a test note 3", self.gov_user, True)
        self.create_case_note(case, "This is a test note 4", self.gov_user, True)

        self.create_case_note(clc_case, "This is a test note 1", self.gov_user, True)
        self.create_case_note(clc_case, "This is a test note 2", self.gov_user, True)
        self.create_case_note(clc_case, "This is a test note 3", self.gov_user, True)

        self.assertEqual(Notification.objects.all().count(), 7)
        self.assertEqual(
            Notification.objects.filter(case_note__case__id=case.id).count(), 4,
        )
        self.assertEqual(
            Notification.objects.filter(case_note__case__id=clc_case.id).count(), 3,
        )

    def tests_get_notifications_for_user_in_multiple_orgs(self):
        """
        Given an exporter user in multiple orgs
        When an API user gets notifications for the exporter user and one of their orgs
        Then the notifications specific to that user and org combination are returned
        """
        org_2, _ = self.create_organisation_with_exporter_user("Org 2")
        self.add_exporter_user_to_org(org_2, self.exporter_user)

        application1 = self.create_standard_application(self.organisation)
        self.submit_application(application1)
        case1 = application1

        self.create_case_note(case1, "This is a test note 1", self.gov_user, True)
        self.create_case_note(case1, "This is a test note 2", self.gov_user, True)

        self.exporter_headers = {
            "HTTP_EXPORTER_USER_TOKEN": user_to_token(self.exporter_user),
            "HTTP_ORGANISATION_ID": org_2.id,
        }

        application2 = self.create_standard_application(org_2)
        self.submit_application(application2)
        case2 = application2

        self.create_case_note(case2, "This is a test note 3", self.gov_user, True)
        self.create_case_note(case2, "This is a test note 4", self.gov_user, True)

        response = self.client.get(self.url, **self.exporter_headers)
        response_data = response.json()["results"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Expecting to only get two of the 4 total notifications created, given that the org in the exporter headers
        # is org_2
        self.assertEqual(len(response_data), 2)
        # Check that the 2 notifications we got are the ones arising from notes on application 2, i.e. the application
        # created while org_2 is the currently selected org
        self.assertEqual(response_data[0]["parent"], str(application2.id))
        self.assertEqual(response_data[1]["parent"], str(application2.id))
