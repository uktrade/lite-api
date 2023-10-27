from unittest import mock

from datetime import time, datetime
from api.audit_trail.models import Audit

from parameterized import parameterized
from freezegun import freeze_time
from django.test import TestCase
from django.utils import timezone

from api.audit_trail.enums import AuditType
from test_helpers.clients import DataTestClient

from api.cases.sla_processing_time import (
    today,
    get_end_date,
    get_start_date,
    daterange,
    is_active_ecju_queries,
    get_all_case_sla,
)


@freeze_time("2020-01-01 12:00:01")
class TodayTestCase(TestCase):
    def test_today_without_time(self):
        output = today()
        self.assertEqual(
            output,
            datetime(2020, 1, 1, 12, 0, 1, tzinfo=timezone.get_current_timezone()),
        )

    def test_today_with_time(self):
        output = today(time=time(1, 0, 1))
        self.assertEqual(
            output,
            datetime(2020, 1, 1, 1, 0, 1, tzinfo=timezone.get_current_timezone()),
        )


class SlaProcessingTimeReport(DataTestClient):
    TODAY = datetime(2020, 2, 12)
    TZINFO = timezone.get_current_timezone()

    def setUp(self):
        super().setUp()
        self.standard_application = self.create_draft_standard_application(self.organisation)
        self.case = self.submit_application(self.standard_application)

    def create_case_submitted_audit_event(self, case):
        return self.create_audit(
            verb=AuditType.UPDATED_STATUS,
            target=case,
            payload={"status": {"new": "submitted"}},
            actor=self.gov_user,
        )

    def create_case_finalised_audit_event(self, case):
        return self.create_audit(
            verb=AuditType.UPDATED_STATUS,
            target=case,
            payload={"status": {"new": "finalised"}},
            actor=self.gov_user,
        )

    @freeze_time("2020-01-01 12:00:01")
    def test_get_end_date_no_audit(self):
        self.assertEqual(
            get_end_date(self.case), datetime.combine(timezone.localtime(), time(17, 0, 0), tzinfo=self.TZINFO)
        )

    @freeze_time("2020-01-05 12:15:01")
    def test_get_end_date_with_audit(self):

        audit = self.create_case_finalised_audit_event(self.case)
        self.assertEqual(get_end_date(self.case), audit.created_at)

    def test_get_end_date(self):
        Audit.objects.filter()
        audit = self.create_case_finalised_audit_event(self.case)
        self.assertEqual(get_end_date(self.case), audit.created_at)

    def test_get_start_date_audit_test(self):

        Audit.objects.filter(target_object_id=self.case.id).delete()
        self.create_audit(
            verb=AuditType.UPDATED_STATUS,
            target=self.case,
            payload={"status": {"new": "unknown"}},
            actor=self.gov_user,
        )

        self.assertEqual(get_start_date(self.case), None)

    def test_date_range(self):
        date_start = datetime(2020, 1, 1, 12, 0, 1, tzinfo=self.TZINFO)
        date_end = datetime(2020, 3, 2, 17, 0, 5, tzinfo=self.TZINFO)
        date_list = list(daterange(date_start, date_end))
        self.assertEqual(len(date_list), 62)
        self.assertEqual(date_list[0], date_start)
        self.assertEqual(date_list[-1], date_end)

    @parameterized.expand(
        [
            (datetime(2020, 1, 1, 12, 0, 1), None, True),
            (datetime(2020, 3, 17, 12, 0, 1), None, True),
            (datetime(2020, 3, 17, 9, 0, 1), datetime(2020, 3, 17, 9, 0, 15), True),
            (datetime(2020, 3, 1, 9, 0, 1), datetime(2020, 3, 19, 9, 0, 15), True),
            (datetime(2020, 1, 1, 12, 0, 1), datetime(2020, 3, 1, 12, 0, 1), False),
            (datetime(2020, 4, 1, 17, 0, 1), datetime(2020, 5, 17, 12, 0, 1), False),
            (datetime(2020, 5, 1, 12, 0, 1), None, False),
        ]
    )
    def test_is_active_ecju_queries(self, query_created_at, query_responded_at, expected):
        query_date = datetime(2020, 3, 17, 12, 0, 1, tzinfo=self.TZINFO)
        self.create_ecju_query(case=self.case, created_at=query_created_at, responded_at=query_responded_at)
        has_queries = is_active_ecju_queries(query_date, self.case.id)
        self.assertEqual(has_queries, expected)

    @parameterized.expand(
        [
            (
                False,
                {
                    "elapsed_days": 33,
                    "working_days": 23,
                    "rfi_queries": 0,
                    "elapsed_rfi_days": 0,
                    "rfi_working_days": 0,
                    "sla_days": 23,
                },
            ),
            (
                True,
                {
                    "elapsed_days": 33,
                    "working_days": 0,
                    "rfi_queries": 0,
                    "elapsed_rfi_days": 0,
                    "rfi_working_days": 0,
                    "sla_days": 0,
                },
            ),
        ]
    )
    @mock.patch("api.cases.sla_processing_time.is_bank_holiday")
    def test_get_case_sla_records_bank_holiday_check_with_no_rfi(
        self, is_bank_holiday, expected_data, mock_is_bank_holiday
    ):

        mock_is_bank_holiday.return_value = is_bank_holiday

        # This create a case that will be 33 calender days
        audit_submitted = self.create_case_submitted_audit_event(self.case)
        audit_submitted.created_at = datetime(2022, 1, 1, 12, 0, 1, tzinfo=self.TZINFO)
        audit_submitted.save()
        audit_finalised = self.create_case_finalised_audit_event(self.case)
        audit_finalised.created_at = datetime(2022, 2, 2, 12, 0, 1, tzinfo=self.TZINFO)
        audit_finalised.save()

        # Add more dynamic data to test
        expected_data["end_date"] = audit_finalised.created_at
        expected_data["start_date"] = audit_submitted.created_at
        expected_data["id"] = self.case.id
        expected_data["reference_code"] = self.case.reference_code

        sla_report = get_all_case_sla()[0]

        for expected_data_key in expected_data.keys():
            self.assertEqual(sla_report[expected_data_key], expected_data[expected_data_key])

    @mock.patch("api.cases.sla_processing_time.is_bank_holiday")
    def test_get_case_sla_records_bank_holiday_check_with_rfi(self, mock_is_bank_holiday):

        # No bank holidays for this test we just checking ECJU time
        mock_is_bank_holiday.return_value = False

        # This create a case that will be 33 calender days
        audit_submitted = self.create_case_submitted_audit_event(self.case)
        audit_submitted.created_at = datetime(2022, 1, 1, 12, 0, 1, tzinfo=self.TZINFO)
        audit_submitted.save()
        audit_finalised = self.create_case_finalised_audit_event(self.case)
        audit_finalised.created_at = datetime(2022, 2, 2, 12, 0, 1, tzinfo=self.TZINFO)
        audit_finalised.save()

        # Create an ECJU Query that spans 7 days
        self.create_ecju_query(
            case=self.case, created_at=datetime(2022, 1, 3, 9, 0, 1), responded_at=datetime(2022, 1, 9, 9, 0, 1)
        )

        expected_data = {
            "id": self.case.id,
            "reference_code": self.case.reference_code,
            "end_date": audit_finalised.created_at,
            "start_date": audit_submitted.created_at,
            "elapsed_days": 33,
            "working_days": 23,
            "rfi_queries": 1,
            "elapsed_rfi_days": 7,
            "rfi_working_days": 5,
            "sla_days": 18,
        }

        sla_report = get_all_case_sla()[0]

        self.assertEqual(sla_report, expected_data)
