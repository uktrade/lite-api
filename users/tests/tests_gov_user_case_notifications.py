from django.urls import reverse_lazy, reverse
from rest_framework import status

from cases.libraries.activity_types import CaseActivityType
from cases.models import Notification, CaseActivity
from test_helpers.clients import DataTestClient


class NotificationTests(DataTestClient):
    def tests_edit_application_creates_new_case_notification_success(self):
        case = self.create_standard_application_case(self.organisation, "Case")
        prev_notification_count = Notification.objects.filter(user=self.gov_user, case_activity__case=case).count()
        url = reverse("applications:application", kwargs={"pk": case.application.id})
        data = {"name": "new app name!"}

        response = self.client.put(url, data, **self.exporter_headers)
        case.refresh_from_db()

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(
            Notification.objects.filter(user=self.gov_user, case_activity__case=case).count(),
            prev_notification_count + 1,
        )

    def tests_edit_application_updates_previous_case_notification_success(self):
        case = self.create_standard_application_case(self.organisation, "Case")
        case_activity = {
            "activity_type": CaseActivityType.UPDATED_APPLICATION_NAME,
            "old_name": "old app name",
            "new_name": "new app name",
        }
        case_activity = CaseActivity.create(case=case, user=self.exporter_user, **case_activity)
        self.gov_user.send_notification(case_activity=case_activity)
        prev_notification_count = Notification.objects.filter(user=self.gov_user, case_activity__case=case).count()
        url = reverse("applications:application", kwargs={"pk": case.application.id})
        data = {"name": "even newer app name!"}

        response = self.client.put(url, data, **self.exporter_headers)
        case.refresh_from_db()
        new_notification = Notification.objects.filter(user=self.gov_user, case_activity__case=case)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(new_notification.count(), prev_notification_count)
        self.assertTrue(data["name"] in new_notification.first().case_activity.text)
        self.assertNotEqual(new_notification.first().case_activity, case_activity)

    def tests_get_case_notification_deletes_case_notification_and_returns_data(self):
        case = self.create_standard_application_case(self.organisation, "Case")
        case_activity = {
            "activity_type": CaseActivityType.UPDATED_APPLICATION_NAME,
            "old_name": "old app name",
            "new_name": "new app name",
        }
        case_activity = CaseActivity.create(case=case, user=self.exporter_user, **case_activity)
        self.gov_user.send_notification(case_activity=case_activity)
        url = reverse_lazy("users:case_notification") + "?case=" + str(case.id)

        response = self.client.get(url, **self.gov_headers)
        notification = response.json()["notification"]

        self.assertEqual(len(notification), 1)
        self.assertEqual(notification["case_activity"], case_activity.id)
        self.assertEqual(
            Notification.objects.filter(user=self.gov_user, case_activity__case=case).count(), 0,
        )

    def tests_edit_application_as_gov_user_does_not_create_a_case_notification(self):
        case = self.create_standard_application_case(self.organisation, "Case")
        prev_notification_count = Notification.objects.filter(user=self.gov_user, case_activity__case=case).count()
        url = reverse("applications:manage_status", kwargs={"pk": case.application.id})
        data = {"status": "under_review"}

        response = self.client.put(url, data, **self.gov_headers)
        case.refresh_from_db()

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(
            Notification.objects.filter(user=self.gov_user, case_activity__case=case).count(), prev_notification_count,
        )
