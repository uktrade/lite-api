from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework import status

from api.audit_trail.models import Audit
from api.staticdata.statuses.enums import CaseStatusEnum
from test_helpers.clients import DataTestClient


class GovUserNotificationTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_draft_standard_application(self.organisation, "Case")
        self.set_application_status(self.case, CaseStatusEnum.APPLICANT_EDITING)
        self.audit_content_type = ContentType.objects.get_for_model(Audit)

    def test_edit_application_creates_new_audit_notification_success(self):
        url = reverse("applications:application", kwargs={"pk": self.case.id})
        data = {"name": "new app name!"}

        response = self.client.put(url, data, **self.exporter_headers)
        self.case.refresh_from_db()

        self.assertEqual(status.HTTP_200_OK, response.status_code)
