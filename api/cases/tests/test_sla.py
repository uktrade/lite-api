from datetime import time, datetime
from unittest import mock
from unittest.mock import patch

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from parameterized import parameterized
from pytz import timezone as tz
from rest_framework import status

from api.cases.enums import CaseTypeEnum, CaseTypeSubTypeEnum
from api.cases.models import Case, CaseQueue, EcjuQuery
from api.cases.tasks import (
    update_cases_sla,
    STANDARD_APPLICATION_TARGET_DAYS,
    OPEN_APPLICATION_TARGET_DAYS,
    MOD_CLEARANCE_TARGET_DAYS,
    SLA_UPDATE_CUTOFF_TIME,
    HMRC_QUERY_TARGET_DAYS,
)
from api.cases.models import CaseAssignmentSla
from test_helpers.clients import DataTestClient

HOUR_BEFORE_CUTOFF = time(SLA_UPDATE_CUTOFF_TIME.hour - 1, 0, 0)
HOUR_AFTER_CUTOFF = time(SLA_UPDATE_CUTOFF_TIME.hour + 1, 0, 0)

TODAY = datetime(2020, 2, 12)
YESTERDAY = datetime(2020, 2, 11)


def _set_submitted_at(case, time, date=timezone.localtime()):
    case.submitted_at = datetime.combine(date, time, tzinfo=tz(settings.TIME_ZONE))
    case.save()


class SlaCaseTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case_types = {
            CaseTypeSubTypeEnum.STANDARD: self.create_draft_standard_application(self.organisation),
            CaseTypeSubTypeEnum.OPEN: self.create_draft_open_application(self.organisation),
            CaseTypeSubTypeEnum.HMRC: self.create_hmrc_query(self.organisation),
            CaseTypeSubTypeEnum.EXHIBITION: self.create_mod_clearance_application(
                self.organisation, CaseTypeEnum.EXHIBITION
            ),
            CaseTypeSubTypeEnum.F680: self.create_mod_clearance_application(self.organisation, CaseTypeEnum.F680),
            CaseTypeSubTypeEnum.GIFTING: self.create_mod_clearance_application(self.organisation, CaseTypeEnum.GIFTING),
            CaseTypeSubTypeEnum.GOODS: self.create_clc_query("abc", self.organisation),
            CaseTypeSubTypeEnum.EUA: self.create_end_user_advisory("abc", "abc", self.organisation),
        }

    @mock.patch("api.cases.tasks.is_weekend")
    @mock.patch("api.cases.tasks.is_bank_holiday")
    def test_sla_update_standard_application(
        self,
        mock_is_weekend,
        mock_is_bank_holiday,
        application_type=CaseTypeSubTypeEnum.STANDARD,
        target=STANDARD_APPLICATION_TARGET_DAYS,
    ):
        mock_is_weekend.return_value = False
        mock_is_bank_holiday.return_value = False
        application = self.case_types[application_type]
        case = self.submit_application(application)
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)

        results = update_cases_sla.now()
        case.refresh_from_db()

        self.assertEqual(results, 1)
        self.assertEqual(case.sla_days, 1)

        self.assertEqual(case.sla_remaining_days, target - 1)

    @mock.patch("api.cases.tasks.is_weekend")
    @mock.patch("api.cases.tasks.is_bank_holiday")
    def test_sla_update_open_application(
        self,
        mock_is_weekend,
        mock_is_bank_holiday,
        application_type=CaseTypeSubTypeEnum.OPEN,
        target=OPEN_APPLICATION_TARGET_DAYS,
    ):
        mock_is_weekend.return_value = False
        mock_is_bank_holiday.return_value = False
        application = self.case_types[application_type]
        case = self.submit_application(application)
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)

        results = update_cases_sla.now()
        case.refresh_from_db()

        self.assertEqual(results, 1)
        self.assertEqual(case.sla_days, 1)
        self.assertEqual(case.sla_remaining_days, target - 1)

    @mock.patch("api.cases.tasks.is_weekend")
    @mock.patch("api.cases.tasks.is_bank_holiday")
    def test_sla_update_hmrc_query(
        self,
        mock_is_weekend,
        mock_is_bank_holiday,
        application_type=CaseTypeSubTypeEnum.HMRC,
        target=HMRC_QUERY_TARGET_DAYS,
    ):
        mock_is_weekend.return_value = False
        mock_is_bank_holiday.return_value = False
        application = self.case_types[application_type]
        case = self.submit_application(application)
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)

        results = update_cases_sla.now()
        case.refresh_from_db()

        self.assertEqual(results, 1)
        self.assertEqual(case.sla_days, 1)
        self.assertEqual(case.sla_remaining_days, target - 1)

    @mock.patch("api.cases.tasks.is_weekend")
    @mock.patch("api.cases.tasks.is_bank_holiday")
    def test_sla_update_exhibition_mod(
        self,
        mock_is_weekend,
        mock_is_bank_holiday,
        application_type=CaseTypeSubTypeEnum.EXHIBITION,
        target=MOD_CLEARANCE_TARGET_DAYS,
    ):
        mock_is_weekend.return_value = False
        mock_is_bank_holiday.return_value = False
        application = self.case_types[application_type]
        case = self.submit_application(application)
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)
        CaseQueue.objects.create(
            case=application.case_ptr, queue=self.queue,
        )
        results = update_cases_sla.now()
        sla = CaseAssignmentSla.objects.get()
        case.refresh_from_db()

        self.assertEqual(sla.sla_days, 1)
        self.assertEqual(results, 1)
        self.assertEqual(case.sla_days, 1)
        self.assertEqual(case.sla_remaining_days, target - 1)

    @mock.patch("api.cases.tasks.is_weekend")
    @mock.patch("api.cases.tasks.is_bank_holiday")
    def test_sla_update_F680_mod(
        self,
        mock_is_weekend,
        mock_is_bank_holiday,
        application_type=CaseTypeSubTypeEnum.F680,
        target=MOD_CLEARANCE_TARGET_DAYS,
    ):
        mock_is_weekend.return_value = False
        mock_is_bank_holiday.return_value = False
        application = self.case_types[application_type]
        case = self.submit_application(application)
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)
        CaseQueue.objects.create(
            queue=self.queue, case=application.case_ptr,
        )
        sla = CaseAssignmentSla.objects.create(sla_days=4, queue=self.queue, case=application.case_ptr,)
        results = update_cases_sla.now()

        case.refresh_from_db()
        sla.refresh_from_db()

        self.assertEqual(sla.sla_days, 5)
        self.assertEqual(results, 1)
        self.assertEqual(case.sla_days, 1)
        self.assertEqual(case.sla_remaining_days, target - 1)

    @mock.patch("api.cases.tasks.is_weekend")
    @mock.patch("api.cases.tasks.is_bank_holiday")
    def test_sla_update_gifting_mod(
        self,
        mock_is_weekend,
        mock_is_bank_holiday,
        application_type=CaseTypeSubTypeEnum.GIFTING,
        target=MOD_CLEARANCE_TARGET_DAYS,
    ):
        mock_is_weekend.return_value = False
        mock_is_bank_holiday.return_value = False
        application = self.case_types[application_type]
        case = self.submit_application(application)
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)

        results = update_cases_sla.now()
        case.refresh_from_db()

        self.assertEqual(results, 1)
        self.assertEqual(case.sla_days, 1)
        self.assertEqual(case.sla_remaining_days, target - 1)

    @parameterized.expand(
        [(CaseTypeSubTypeEnum.GOODS,), (CaseTypeSubTypeEnum.EUA,),]
    )
    def test_sla_doesnt_update_queries(self, query_type):
        query = self.case_types[query_type]
        case = self.submit_application(query)
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)

        results = update_cases_sla.now()
        case.refresh_from_db()

        self.assertEqual(results, 0)
        self.assertEqual(case.sla_days, 0)
        self.assertEqual(case.sla_remaining_days, None)


class SlaRulesTests(DataTestClient):
    @mock.patch("api.cases.tasks.is_weekend")
    @mock.patch("api.cases.tasks.is_bank_holiday")
    def test_sla_cutoff_window(self, mock_is_weekend, mock_is_bank_holiday):
        mock_is_weekend.return_value = False
        mock_is_bank_holiday.return_value = False
        times = [
            HOUR_BEFORE_CUTOFF,
            SLA_UPDATE_CUTOFF_TIME,
            HOUR_AFTER_CUTOFF,
        ]
        for submit_time in times:
            application = self.create_draft_standard_application(self.organisation)
            case = self.submit_application(application)
            _set_submitted_at(case, submit_time)

        results = update_cases_sla.now()
        cases = Case.objects.all().order_by("submitted_at")

        self.assertEqual(results, 1)
        self.assertEqual(cases[0].sla_days, 1)
        self.assertEqual(cases[1].sla_days, 0)
        self.assertEqual(cases[2].sla_days, 0)

    def test_sla_ignores_previously_finalised_cases(self):
        application = self.create_draft_standard_application(self.organisation)
        case = self.submit_application(application)
        case.last_closed_at = timezone.now()
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)

        results = update_cases_sla.now()
        case.refresh_from_db()

        self.assertEqual(results, 0)
        self.assertEqual(case.sla_days, 0)

    def test_sla_does_not_apply_sla_twice_in_one_day(self):
        application = self.create_draft_standard_application(self.organisation)
        case = self.submit_application(application)
        case.sla_updated_at = timezone.now()
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)

        results = update_cases_sla.now()
        case.refresh_from_db()

        self.assertEqual(results, 0)
        self.assertEqual(case.sla_days, 0)

    @mock.patch("api.cases.tasks.is_weekend")
    @mock.patch("api.cases.tasks.is_bank_holiday")
    def test_unanswered_ecju_queries_today_before_cutoff(
        self,
        mock_is_weekend,
        mock_is_bank_holiday,
        created_at=datetime.combine(TODAY, time=HOUR_BEFORE_CUTOFF, tzinfo=timezone.utc),
        expected_results=0,
    ):
        mock_is_weekend.return_value = False
        mock_is_bank_holiday.return_value = False
        case = self.create_standard_application_case(self.organisation)
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)
        self.create_ecju_query(case)
        EcjuQuery.objects.all().update(created_at=created_at)

        with patch(
            "api.cases.tasks.today",
            return_value=datetime.combine(TODAY, time=SLA_UPDATE_CUTOFF_TIME, tzinfo=timezone.utc),
        ):
            results = update_cases_sla.now()
        case.refresh_from_db()

        self.assertEqual(results, expected_results)
        self.assertEqual(case.sla_days, expected_results)

    @mock.patch("api.cases.tasks.is_weekend")
    @mock.patch("api.cases.tasks.is_bank_holiday")
    def test_unanswered_ecju_queries_today_after_cutoff(
        self,
        mock_is_weekend,
        mock_is_bank_holiday,
        created_at=datetime.combine(TODAY, time=HOUR_AFTER_CUTOFF, tzinfo=timezone.utc),
        expected_results=1,
    ):
        mock_is_weekend.return_value = False
        mock_is_bank_holiday.return_value = False
        case = self.create_standard_application_case(self.organisation)
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)
        self.create_ecju_query(case)
        EcjuQuery.objects.all().update(created_at=created_at)

        with patch(
            "api.cases.tasks.today",
            return_value=datetime.combine(TODAY, time=SLA_UPDATE_CUTOFF_TIME, tzinfo=timezone.utc),
        ):
            results = update_cases_sla.now()
        case.refresh_from_db()

        self.assertEqual(results, expected_results)
        self.assertEqual(case.sla_days, expected_results)

    @mock.patch("api.cases.tasks.is_weekend")
    @mock.patch("api.cases.tasks.is_bank_holiday")
    def test_unanswered_ecju_queries_yesterday_before_cutoff(
        self,
        mock_is_weekend,
        mock_is_bank_holiday,
        created_at=datetime.combine(YESTERDAY, time=HOUR_BEFORE_CUTOFF, tzinfo=timezone.utc),
        expected_results=0,
    ):
        mock_is_weekend.return_value = False
        mock_is_bank_holiday.return_value = False
        case = self.create_standard_application_case(self.organisation)
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)
        self.create_ecju_query(case)
        EcjuQuery.objects.all().update(created_at=created_at)

        with patch(
            "api.cases.tasks.today",
            return_value=datetime.combine(TODAY, time=SLA_UPDATE_CUTOFF_TIME, tzinfo=timezone.utc),
        ):
            results = update_cases_sla.now()
        case.refresh_from_db()

        self.assertEqual(results, expected_results)
        self.assertEqual(case.sla_days, expected_results)

    @mock.patch("api.cases.tasks.is_weekend")
    @mock.patch("api.cases.tasks.is_bank_holiday")
    def test_unanswered_ecju_queries_yesterday_after_cutoff(
        self,
        mock_is_weekend,
        mock_is_bank_holiday,
        created_at=datetime.combine(YESTERDAY, time=HOUR_AFTER_CUTOFF, tzinfo=timezone.utc),
        expected_results=0,
    ):
        mock_is_weekend.return_value = False
        mock_is_bank_holiday.return_value = False
        case = self.create_standard_application_case(self.organisation)
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)
        self.create_ecju_query(case)
        EcjuQuery.objects.all().update(created_at=created_at)

        with patch(
            "api.cases.tasks.today",
            return_value=datetime.combine(TODAY, time=SLA_UPDATE_CUTOFF_TIME, tzinfo=timezone.utc),
        ):
            results = update_cases_sla.now()
        case.refresh_from_db()

        self.assertEqual(results, expected_results)
        self.assertEqual(case.sla_days, expected_results)

    @mock.patch("api.cases.tasks.is_weekend")
    @mock.patch("api.cases.tasks.is_bank_holiday")
    def test_answered_ecju_queries_today_before_cutoff(
        self,
        mock_is_weekend,
        mock_is_bank_holiday,
        responded_at=datetime.combine(TODAY, time=HOUR_BEFORE_CUTOFF, tzinfo=timezone.utc),
        expected_results=0,
    ):
        mock_is_weekend.return_value = False
        mock_is_bank_holiday.return_value = False
        case = self.create_standard_application_case(self.organisation)
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)
        query = self.create_ecju_query(case)
        query.created_at = datetime.combine(TODAY, time=HOUR_BEFORE_CUTOFF, tzinfo=timezone.utc)
        query.responded_at = responded_at
        query.save()

        with patch(
            "api.cases.tasks.yesterday",
            return_value=datetime.combine(YESTERDAY, time=SLA_UPDATE_CUTOFF_TIME, tzinfo=timezone.utc),
        ):
            results = update_cases_sla.now()
        case.refresh_from_db()

        self.assertEqual(results, expected_results)
        self.assertEqual(case.sla_days, expected_results)

    @mock.patch("api.cases.tasks.is_weekend")
    @mock.patch("api.cases.tasks.is_bank_holiday")
    def test_answered_ecju_queries_today_after_cutoff(
        self,
        mock_is_weekend,
        mock_is_bank_holiday,
        responded_at=datetime.combine(TODAY, time=HOUR_AFTER_CUTOFF, tzinfo=timezone.utc),
        expected_results=0,
    ):
        mock_is_weekend.return_value = False
        mock_is_bank_holiday.return_value = False
        case = self.create_standard_application_case(self.organisation)
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)
        query = self.create_ecju_query(case)
        query.created_at = datetime.combine(TODAY, time=HOUR_BEFORE_CUTOFF, tzinfo=timezone.utc)
        query.responded_at = responded_at
        query.save()

        with patch(
            "api.cases.tasks.yesterday",
            return_value=datetime.combine(YESTERDAY, time=SLA_UPDATE_CUTOFF_TIME, tzinfo=timezone.utc),
        ):
            results = update_cases_sla.now()
        case.refresh_from_db()

        self.assertEqual(results, expected_results)
        self.assertEqual(case.sla_days, expected_results)

    @mock.patch("api.cases.tasks.is_weekend")
    @mock.patch("api.cases.tasks.is_bank_holiday")
    def test_answered_ecju_queries_yesterday_before_cutoff(
        self,
        mock_is_weekend,
        mock_is_bank_holiday,
        responded_at=datetime.combine(YESTERDAY, time=HOUR_BEFORE_CUTOFF, tzinfo=timezone.utc),
        expected_results=0,
    ):
        mock_is_weekend.return_value = False
        mock_is_bank_holiday.return_value = False
        case = self.create_standard_application_case(self.organisation)
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)
        query = self.create_ecju_query(case)
        query.created_at = datetime.combine(TODAY, time=HOUR_BEFORE_CUTOFF, tzinfo=timezone.utc)
        query.responded_at = responded_at
        query.save()

        with patch(
            "api.cases.tasks.yesterday",
            return_value=datetime.combine(YESTERDAY, time=SLA_UPDATE_CUTOFF_TIME, tzinfo=timezone.utc),
        ):
            results = update_cases_sla.now()
        case.refresh_from_db()

        self.assertEqual(results, expected_results)
        self.assertEqual(case.sla_days, expected_results)

    @mock.patch("api.cases.tasks.is_weekend")
    @mock.patch("api.cases.tasks.is_bank_holiday")
    def test_answered_ecju_queries_yesterday_after_cutoff(
        self,
        mock_is_weekend,
        mock_is_bank_holiday,
        responded_at=datetime.combine(YESTERDAY, time=HOUR_AFTER_CUTOFF, tzinfo=timezone.utc),
        expected_results=0,
    ):
        mock_is_weekend.return_value = False
        mock_is_bank_holiday.return_value = False
        case = self.create_standard_application_case(self.organisation)
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)
        query = self.create_ecju_query(case)
        query.created_at = datetime.combine(TODAY, time=HOUR_BEFORE_CUTOFF, tzinfo=timezone.utc)
        query.responded_at = responded_at
        query.save()

        with patch(
            "api.cases.tasks.yesterday",
            return_value=datetime.combine(YESTERDAY, time=SLA_UPDATE_CUTOFF_TIME, tzinfo=timezone.utc),
        ):
            results = update_cases_sla.now()
        case.refresh_from_db()

        self.assertEqual(results, expected_results)
        self.assertEqual(case.sla_days, expected_results)


class WorkingDayTests(DataTestClient):
    @mock.patch("api.cases.tasks.is_weekend")
    @mock.patch("api.cases.tasks.is_bank_holiday")
    def test_weekends_ignored(self, weekend_func, bank_holiday_func):
        weekend_func.return_value = True
        bank_holiday_func.return_value = False

        result = update_cases_sla.now()

        self.assertFalse(result)

    @mock.patch("api.cases.tasks.is_weekend")
    @mock.patch("api.cases.tasks.is_bank_holiday")
    def test_bank_holidays_ignored(self, weekend_func, bank_holiday_func):
        weekend_func.return_value = False
        bank_holiday_func.return_value = True

        result = update_cases_sla.now()

        self.assertFalse(result)

    @mock.patch("api.cases.tasks.is_weekend")
    @mock.patch("api.cases.tasks.is_bank_holiday")
    def test_bank_holiday_weekend_ignored(self, weekend_func, bank_holiday_func):
        weekend_func.return_value = False
        bank_holiday_func.return_value = False

        result = update_cases_sla.now()

        # Expecting update_cases_sla to be ran, but no cases found
        self.assertEqual(result, 0)


class SlaHmrcCaseTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.hmrc_query = self.create_hmrc_query(self.organisation)
        self.submit_application(self.hmrc_query)
        self.url = reverse("cases:search")

    def test_sla_hours_appears_on_hmrc_queries_when_goods_not_yet_left_country(self):
        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["results"]["cases"]
        self.assertIn("sla_hours_since_raised", response_data[0])

    def test_sla_hours_does_not_appear_on_hmrc_queries_when_goods_have_left_country(self):
        self.hmrc_query.have_goods_departed = True
        self.hmrc_query.save()

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["results"]["cases"]
        self.assertNotIn("sla_hours_since_raised", response_data[0])

    def test_sla_hours_does_not_appear_on_other_cases(self):
        self.hmrc_query.delete()
        self.create_standard_application_case(self.organisation)

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["results"]["cases"]
        self.assertNotIn("sla_hours_since_raised", response_data[0])


class TerminalCaseSlaTests(DataTestClient):
    @mock.patch("api.cases.tasks.is_weekend")
    @mock.patch("api.cases.tasks.is_bank_holiday")
    def test_sla_not_update_for_terminal(
        self, mock_is_weekend, mock_is_bank_holiday,
    ):
        mock_is_weekend.return_value = False
        mock_is_bank_holiday.return_value = False
        application = self.create_draft_standard_application(self.organisation)
        case = self.submit_application(application)
        _set_submitted_at(case, HOUR_BEFORE_CUTOFF)

        results = update_cases_sla.now()
        case.refresh_from_db()
        self.assertEqual(results, 1)
        self.assertEqual(case.sla_days, 1)
        self.assertEqual(case.sla_remaining_days, STANDARD_APPLICATION_TARGET_DAYS - 1)

        for case_status in CaseStatusEnum.terminal_statuses():
            application.status = get_case_status_by_status(case_status)
            application.save()

            results = update_cases_sla.now()
            case.refresh_from_db()
            self.assertEqual(results, 0)
            self.assertEqual(case.sla_days, 1)
            self.assertEqual(case.sla_remaining_days, STANDARD_APPLICATION_TARGET_DAYS - 1)
