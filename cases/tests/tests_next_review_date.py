from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from audit_trail.enums import AuditType
from audit_trail.models import Audit
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
        self.assertEqual(audit_qs.first().payload, {"old_ref_number": "no reference"})

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

    def test_add_invalid_type_next_review_date_failure(self):
        date = "Invalid date format"
        request = self.client.put(self.url, data={"next_review_date": date}, **self.gov_headers)

        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(request.data["errors"]["next_review_date"][0]), strings.Cases.NextReviewDate.Errors.INVALID_DATE_FORMAT
        )
        self.assertEqual(len(self.case.case_review_date.all()), 0)

    def test_add_invalid_format_next_review_date_failure(self):
        date = "2025-13-40"
        request = self.client.put(self.url, data={"next_review_date": date}, **self.gov_headers)

        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(request.data["errors"]["next_review_date"][0]), strings.Cases.NextReviewDate.Errors.INVALID_DATE_FORMAT
        )
        self.assertEqual(len(self.case.case_review_date.all()), 0)

    def test_add_past_next_review_date_failure(self):
        date = "2000-01-01"
        request = self.client.put(self.url, data={"next_review_date": date}, **self.gov_headers)

        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(request.data["errors"]["next_review_date"][0]), strings.Cases.NextReviewDate.Errors.DATE_IN_PAST
        )
        self.assertEqual(len(self.case.case_review_date.all()), 0)
