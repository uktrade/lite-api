from django.contrib.contenttypes.models import ContentType
from django.urls import reverse_lazy, reverse
from rest_framework import status

from audit_trail.models import Audit
from audit_trail.payload import AuditType
from users.models import GovNotification
from test_helpers.clients import DataTestClient


class NotificationTests(DataTestClient):
    def tests_edit_application_creates_new_case_notification_success(self):
        case = self.create_standard_application_case(self.organisation, "Case")
        content_type = ContentType.objects.get_for_model(Audit)

        prev_notification_count = GovNotification.objects.filter(
            user=self.gov_user, content_type=content_type, case=case
        ).count()

        url = reverse("applications:application", kwargs={"pk": case.id})
        data = {"name": "new app name!"}

        response = self.client.put(url, data, **self.exporter_headers)
        case.refresh_from_db()

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(
            GovNotification.objects.filter(user=self.gov_user, content_type=content_type, case=case).count(),
            prev_notification_count + 1,
        )

    def tests_edit_application_updates_previous_case_notification_success(self):
        case = self.create_standard_application_case(self.organisation, "Case")
        content_type = ContentType.objects.get_for_model(Audit)

        audit = Audit.objects.create(
            actor=self.exporter_user,
            verb=AuditType.UPDATED_APPLICATION_NAME,
            target=case,
            payload={"old_name": "old_app_name", "new_name": "new_app_name"},
        )

        self.gov_user.send_notification(content_object=audit, case=case)
        prev_notification_count = GovNotification.objects.filter(
            user=self.gov_user, content_type=content_type, case=case
        ).count()

        url = reverse("applications:application", kwargs={"pk": case.id})
        data = {"name": "even newer app name!"}

        response = self.client.put(url, data, **self.exporter_headers)
        case.refresh_from_db()
        case.refresh_from_db()

        new_notification = GovNotification.objects.filter(user=self.gov_user, content_type=content_type, case=case)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(new_notification.count(), prev_notification_count)
        self.assertEqual(data["name"], new_notification.last().content_object.payload["new_name"])
        self.assertNotEqual(new_notification.last().content_object, audit)

    def tests_get_case_notification_deletes_case_notification_and_returns_data(self):
        case = self.create_standard_application_case(self.organisation, "Case")
        content_type = ContentType.objects.get_for_model(Audit)

        audit = Audit.objects.create(
            actor=self.exporter_user,
            verb=AuditType.UPDATED_APPLICATION_NAME,
            target=case,
            payload={"old_name": "old_app_name", "new_name": "new_app_name"},
        )

        self.gov_user.send_notification(content_object=audit, case=case)
        url = reverse_lazy("users:case_notification") + "?case=" + str(case.id)

        response = self.client.get(url, **self.gov_headers)
        notification = response.json()["notification"]

        self.assertEqual(len(notification), 1)
        self.assertEqual(notification["audit_id"], str(audit.id))

        self.assertEqual(
            GovNotification.objects.filter(user=self.gov_user, content_type=content_type, case=case).count(), 0,
        )

    def tests_edit_application_as_gov_user_does_not_create_a_case_notification(self):
        case = self.create_standard_application_case(self.organisation, "Case")
        content_type = ContentType.objects.get_for_model(Audit)
        prev_notification_count = GovNotification.objects.filter(
            user=self.gov_user, content_type=content_type, case=case
        ).count()
        url = reverse("applications:manage_status", kwargs={"pk": case.id})

        data = {"status": "under_review"}

        response = self.client.put(url, data, **self.gov_headers)
        case.refresh_from_db()

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(
            GovNotification.objects.filter(user=self.gov_user, content_type=content_type, case=case).count(),
            prev_notification_count,
        )
