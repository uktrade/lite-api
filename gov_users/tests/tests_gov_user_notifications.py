from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework import status

from audit_trail.models import Audit
from audit_trail.payload import AuditType
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from users.models import GovNotification
from test_helpers.clients import DataTestClient


class GovUserNotificationTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_standard_application_case(self.organisation, "Case")
        self.audit_content_type = ContentType.objects.get_for_model(Audit)

    def test_edit_application_creates_new_audit_notification_success(self):
        prev_case_audit_notification_count = GovNotification.objects.filter(
            user=self.gov_user, content_type=self.audit_content_type, case=self.case
        ).count()

        url = reverse("applications:application", kwargs={"pk": self.case.id})
        data = {"name": "new app name!"}

        response = self.client.put(url, data, **self.exporter_headers)
        self.case.refresh_from_db()
        case_audit_notification_count = GovNotification.objects.filter(
            user=self.gov_user, content_type=self.audit_content_type, case=self.case
        ).count()

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(case_audit_notification_count, prev_case_audit_notification_count + 1)

    def test_edit_application_updates_previous_audit_notification_success(self):
        audit = Audit.objects.create(
            actor=self.exporter_user,
            verb=AuditType.UPDATED_APPLICATION_NAME.value,
            target=self.case.get_case(),
            payload={"old_name": "old_app_name", "new_name": "new_app_name"},
        )

        self.gov_user.send_notification(content_object=audit, case=self.case)
        prev_case_audit_notification_count = GovNotification.objects.filter(
            user=self.gov_user, content_type=self.audit_content_type, case=self.case
        ).count()

        url = reverse("applications:application", kwargs={"pk": self.case.id})
        data = {"name": "even newer app name!"}

        response = self.client.put(url, data, **self.exporter_headers)
        self.case.refresh_from_db()
        case_audit_notification = GovNotification.objects.filter(
            user=self.gov_user, content_type=self.audit_content_type, case=self.case
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(case_audit_notification.count(), prev_case_audit_notification_count)
        self.assertEqual(data["name"], case_audit_notification.last().content_object.payload["new_name"])
        self.assertNotEqual(case_audit_notification.last().content_object, audit)

    def test_edit_application_as_gov_user_does_not_create_an_audit_notification_success(self):
        prev_case_audit_notification_count = GovNotification.objects.filter(
            user=self.gov_user, content_type=self.audit_content_type, case=self.case
        ).count()
        url = reverse("applications:manage_status", kwargs={"pk": self.case.id})
        data = {"status": "under_review"}

        response = self.client.put(url, data, **self.gov_headers)
        self.case.refresh_from_db()
        case_audit_notification_count = GovNotification.objects.filter(
            user=self.gov_user, content_type=self.audit_content_type, case=self.case
        ).count()

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(case_audit_notification_count, prev_case_audit_notification_count)

    def test_get_case_deletes_audit_notification_success(self):
        self.case = self.create_standard_application_case(self.organisation).get_case()
        self.case.status = get_case_status_by_status(CaseStatusEnum.APPLICANT_EDITING)
        self.case.save()
        audit = Audit.objects.create(
            actor=self.exporter_user,
            verb=AuditType.UPDATED_STATUS.value,
            target=self.case,
            payload={"status": CaseStatusEnum.APPLICANT_EDITING},
        )

        self.gov_user.send_notification(content_object=audit, case=self.case)
        url = reverse("cases:activity", kwargs={"pk": self.case.id})

        response = self.client.get(url, **self.gov_headers)
        case_audit_notification_count = GovNotification.objects.filter(
            user=self.gov_user, content_type=self.audit_content_type, case=self.case
        ).count()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        case_activity = response.json()["activity"]
        self.assertEqual(len(case_activity), 1)
        self.assertEqual(case_audit_notification_count, 0)
