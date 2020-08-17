from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.core.helpers import convert_date_to_string
from lite_content.lite_api import strings
from test_helpers.clients import DataTestClient


class NextReviewDateTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_draft_standard_application(self.organisation)
        self.case = self.submit_application(self.standard_application)
        self.user = self.create_gov_user("new_user@their.email.com", self.team)
        self.url = reverse("cases:review_date", kwargs={"pk": self.case.id})

    def test_add_next_review_date_success(self):
        date = "2025-06-30"
        request = self.client.put(self.url, data={"next_review_date": date}, **self.gov_headers)

        self.assertEqual(request.status_code, status.HTTP_200_OK)
        self.case.refresh_from_db()
        case_review_date = self.case.case_review_date.all()[0]

        self.assertEqual(len(self.case.case_review_date.all()), 1)
        self.assertEqual(str(case_review_date.next_review_date), date)
        self.assertEqual(case_review_date.team_id, self.team.id)
        self.assertEqual(case_review_date.case_id, self.case.id)

        audit_qs = Audit.objects.all()
        self.assertEqual(audit_qs.count(), 2)
        self.assertEqual(AuditType(audit_qs.first().verb), AuditType.ADDED_NEXT_REVIEW_DATE)
        self.assertEqual(
            audit_qs.first().payload, {"next_review_date": convert_date_to_string(date), "team_name": self.team.name}
        )

    def test_add_present_next_review_date_success(self):
        date = timezone.now().date()
        request = self.client.put(self.url, data={"next_review_date": str(date)}, **self.gov_headers)

        self.assertEqual(request.status_code, status.HTTP_200_OK)
        self.case.refresh_from_db()
        case_review_date = self.case.case_review_date.all()[0]

        self.assertEqual(len(self.case.case_review_date.all()), 1)
        self.assertEqual(case_review_date.next_review_date, date)
        self.assertEqual(case_review_date.team_id, self.team.id)
        self.assertEqual(case_review_date.case_id, self.case.id)

        audit_qs = Audit.objects.all()
        self.assertEqual(audit_qs.count(), 2)
        self.assertEqual(AuditType(audit_qs.first().verb), AuditType.ADDED_NEXT_REVIEW_DATE)
        self.assertEqual(
            audit_qs.first().payload, {"next_review_date": convert_date_to_string(date), "team_name": self.team.name}
        )

    def test_add_blank_next_review_date_success(self):
        date = None
        request = self.client.put(self.url, data={"next_review_date": date}, **self.gov_headers)

        self.assertEqual(request.status_code, status.HTTP_200_OK)
        self.case.refresh_from_db()
        case_review_date = self.case.case_review_date.all()[0]

        self.assertEqual(len(self.case.case_review_date.all()), 1)
        self.assertEqual(case_review_date.next_review_date, date)
        self.assertEqual(case_review_date.team_id, self.team.id)
        self.assertEqual(case_review_date.case_id, self.case.id)

        audit_qs = Audit.objects.all()
        self.assertEqual(audit_qs.count(), 1)
        self.assertNotEqual(AuditType(audit_qs.first().verb), AuditType.ADDED_NEXT_REVIEW_DATE)

    def test_clear_next_review_date_success(self):
        date = "2025-01-01"
        request = self.client.put(self.url, data={"next_review_date": date}, **self.gov_headers)

        self.assertEqual(request.status_code, status.HTTP_200_OK)
        self.case.refresh_from_db()

        case_review_date = self.case.case_review_date.all()[0]
        self.assertEqual(len(self.case.case_review_date.all()), 1)
        self.assertEqual(str(case_review_date.next_review_date), date)
        self.assertEqual(case_review_date.team_id, self.team.id)
        self.assertEqual(case_review_date.case_id, self.case.id)

        audit_qs = Audit.objects.all()
        self.assertEqual(audit_qs.count(), 2)
        self.assertEqual(AuditType(audit_qs.first().verb), AuditType.ADDED_NEXT_REVIEW_DATE)
        self.assertEqual(
            audit_qs.first().payload, {"next_review_date": convert_date_to_string(date), "team_name": self.team.name}
        )

        date = None
        request = self.client.put(self.url, data={"next_review_date": date}, **self.gov_headers)

        self.assertEqual(request.status_code, status.HTTP_200_OK)
        self.case.refresh_from_db()

        case_review_date = self.case.case_review_date.all()[0]
        self.assertEqual(len(self.case.case_review_date.all()), 1)
        self.assertEqual(case_review_date.next_review_date, date)
        self.assertEqual(case_review_date.team_id, self.team.id)
        self.assertEqual(case_review_date.case_id, self.case.id)

        audit_qs = Audit.objects.all()
        self.assertEqual(audit_qs.count(), 3)
        self.assertEqual(AuditType(audit_qs.first().verb), AuditType.REMOVED_NEXT_REVIEW_DATE)
        self.assertEqual(audit_qs.first().payload, {"team_name": self.team.name})

    def test_change_next_review_date_success(self):
        old_date = "2025-01-01"
        request = self.client.put(self.url, data={"next_review_date": old_date}, **self.gov_headers)

        self.assertEqual(request.status_code, status.HTTP_200_OK)
        self.case.refresh_from_db()

        case_review_date = self.case.case_review_date.all()[0]
        self.assertEqual(len(self.case.case_review_date.all()), 1)
        self.assertEqual(str(case_review_date.next_review_date), old_date)
        self.assertEqual(case_review_date.team_id, self.team.id)
        self.assertEqual(case_review_date.case_id, self.case.id)

        audit_qs = Audit.objects.all()
        self.assertEqual(audit_qs.count(), 2)
        self.assertEqual(AuditType(audit_qs.first().verb), AuditType.ADDED_NEXT_REVIEW_DATE)
        self.assertEqual(
            audit_qs.first().payload,
            {"next_review_date": convert_date_to_string(old_date), "team_name": self.team.name},
        )

        new_date = "2026-05-06"
        request = self.client.put(self.url, data={"next_review_date": new_date}, **self.gov_headers)

        self.assertEqual(request.status_code, status.HTTP_200_OK)
        self.case.refresh_from_db()

        case_review_date = self.case.case_review_date.all()[0]
        self.assertEqual(len(self.case.case_review_date.all()), 1)
        self.assertEqual(str(case_review_date.next_review_date), new_date)
        self.assertEqual(case_review_date.team_id, self.team.id)
        self.assertEqual(case_review_date.case_id, self.case.id)

        audit_qs = Audit.objects.all()
        self.assertEqual(audit_qs.count(), 3)
        self.assertEqual(AuditType(audit_qs.first().verb), AuditType.EDITED_NEXT_REVIEW_DATE)
        self.assertEqual(
            audit_qs.first().payload,
            {
                "old_date": convert_date_to_string(old_date),
                "new_date": convert_date_to_string(new_date),
                "team_name": self.team.name,
            },
        )

    def test_resubmit_same_next_review_date_success(self):
        date = "2025-01-01"
        request = self.client.put(self.url, data={"next_review_date": date}, **self.gov_headers)

        self.assertEqual(request.status_code, status.HTTP_200_OK)
        self.case.refresh_from_db()

        case_review_date = self.case.case_review_date.all()[0]
        self.assertEqual(len(self.case.case_review_date.all()), 1)
        self.assertEqual(str(case_review_date.next_review_date), date)
        self.assertEqual(case_review_date.team_id, self.team.id)
        self.assertEqual(case_review_date.case_id, self.case.id)

        audit_qs = Audit.objects.all()
        self.assertEqual(audit_qs.count(), 2)
        self.assertEqual(AuditType(audit_qs.first().verb), AuditType.ADDED_NEXT_REVIEW_DATE)
        self.assertEqual(
            audit_qs.first().payload, {"next_review_date": convert_date_to_string(date), "team_name": self.team.name}
        )

        request = self.client.put(self.url, data={"next_review_date": date}, **self.gov_headers)

        self.assertEqual(request.status_code, status.HTTP_200_OK)
        self.case.refresh_from_db()

        case_review_date = self.case.case_review_date.all()[0]
        self.assertEqual(len(self.case.case_review_date.all()), 1)
        self.assertEqual(str(case_review_date.next_review_date), date)
        self.assertEqual(case_review_date.team_id, self.team.id)
        self.assertEqual(case_review_date.case_id, self.case.id)

        audit_qs = Audit.objects.all()
        # Resubmitting the same date shouldn't created an new edited audit
        self.assertEqual(audit_qs.count(), 2)
        self.assertNotEqual(AuditType(audit_qs.first().verb), AuditType.EDITED_NEXT_REVIEW_DATE)

    def test_add_invalid_type_next_review_date_failure(self):
        date = "YYYY-mm-dd"
        request = self.client.put(self.url, data={"next_review_date": date}, **self.gov_headers)

        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(request.data["errors"]["next_review_date"][0]), strings.Cases.NextReviewDate.Errors.INVALID_DATE_FORMAT
        )
        self.assertEqual(len(self.case.case_review_date.all()), 0)

        audit_qs = Audit.objects.all()
        self.assertEqual(audit_qs.count(), 1)
        self.assertNotEqual(AuditType(audit_qs.first().verb), AuditType.ADDED_NEXT_REVIEW_DATE)

    def test_add_invalid_format_next_review_date_failure(self):
        date = "2025-13-40"
        request = self.client.put(self.url, data={"next_review_date": date}, **self.gov_headers)

        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(request.data["errors"]["next_review_date"][0]), strings.Cases.NextReviewDate.Errors.INVALID_DATE_FORMAT
        )
        self.assertEqual(len(self.case.case_review_date.all()), 0)

        audit_qs = Audit.objects.all()
        self.assertEqual(audit_qs.count(), 1)
        self.assertNotEqual(AuditType(audit_qs.first().verb), AuditType.ADDED_NEXT_REVIEW_DATE)

    def test_add_past_next_review_date_failure(self):
        date = "2000-01-01"
        request = self.client.put(self.url, data={"next_review_date": date}, **self.gov_headers)

        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(request.data["errors"]["next_review_date"][0]), strings.Cases.NextReviewDate.Errors.DATE_IN_PAST
        )
        self.assertEqual(len(self.case.case_review_date.all()), 0)

        audit_qs = Audit.objects.all()
        self.assertEqual(audit_qs.count(), 1)
        self.assertNotEqual(AuditType(audit_qs.first().verb), AuditType.ADDED_NEXT_REVIEW_DATE)
