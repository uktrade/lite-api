from datetime import date, time
from unittest import mock

from django.test import tag
from django.utils import timezone
from parameterized import parameterized

from cases.enums import CaseTypeEnum, CaseTypeSubTypeEnum
from cases.models import Case
from cases.sla import (
    update_cases_sla,
    is_weekend,
    is_bank_holiday,
    STANDARD_APPLICATION_TARGET_DAYS,
    OPEN_APPLICATION_TARGET_DAYS,
    MOD_CLEARANCE_TARGET_DAYS,
    SLA_UPDATE_CUTOFF_TIME,
    yesterday,
)
from test_helpers.clients import DataTestClient


def _set_case_time(case, time, date=timezone.now()):
    case.submitted_at = timezone.datetime.combine(date, time)
    case.save()


def _set_response_time(case, time, date=timezone.now()):
    case.responded_at = timezone.datetime.combine(date, time)
    case.save()


class SlaCaseTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.hour_before_cutoff = time(SLA_UPDATE_CUTOFF_TIME.hour - 1, 0, 0)
        self.case_types = {
            CaseTypeSubTypeEnum.STANDARD: self.create_draft_standard_application(self.organisation),
            CaseTypeSubTypeEnum.OPEN: self.create_open_application(self.organisation),
            CaseTypeSubTypeEnum.EXHIBITION: self.create_mod_clearance_application(
                self.organisation, CaseTypeEnum.EXHIBITION
            ),
            CaseTypeSubTypeEnum.F680: self.create_mod_clearance_application(self.organisation, CaseTypeEnum.F680),
            CaseTypeSubTypeEnum.GIFTING: self.create_mod_clearance_application(self.organisation, CaseTypeEnum.GIFTING),
            CaseTypeSubTypeEnum.GOODS: self.create_clc_query("abc", self.organisation),
            CaseTypeSubTypeEnum.EUA: self.create_end_user_advisory("abc", "abc", self.organisation),
        }

    @parameterized.expand(
        [
            (CaseTypeSubTypeEnum.STANDARD, STANDARD_APPLICATION_TARGET_DAYS),
            (CaseTypeSubTypeEnum.OPEN, OPEN_APPLICATION_TARGET_DAYS),
            (CaseTypeSubTypeEnum.EXHIBITION, MOD_CLEARANCE_TARGET_DAYS),
            (CaseTypeSubTypeEnum.F680, MOD_CLEARANCE_TARGET_DAYS),
            (CaseTypeSubTypeEnum.GIFTING, MOD_CLEARANCE_TARGET_DAYS),
        ]
    )
    def test_sla_update_application(self, application_type, target):
        application = self.case_types[application_type]
        case = self.submit_application(application)
        _set_case_time(case, self.hour_before_cutoff)

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
        _set_case_time(case, self.hour_before_cutoff)

        results = update_cases_sla.now()
        case.refresh_from_db()

        self.assertEqual(results, 0)
        self.assertEqual(case.sla_days, 0)
        self.assertEqual(case.sla_remaining_days, None)


class SlaRulesTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.hour_before_cutoff = time(SLA_UPDATE_CUTOFF_TIME.hour - 1, 0, 0)
        self.hour_after_cutoff = time(SLA_UPDATE_CUTOFF_TIME.hour + 1, 0, 0)

    @tag("987")
    def test_sla_cutoff_window(self):
        times = [
            self.hour_before_cutoff,
            SLA_UPDATE_CUTOFF_TIME,
            self.hour_after_cutoff,
        ]
        for submit_time in times:
            application = self.create_draft_standard_application(self.organisation)
            case = self.submit_application(application)
            _set_case_time(case, submit_time)

        results = update_cases_sla.now()
        cases = Case.objects.all().order_by("submitted_at")

        self.assertEqual(results, 1)
        self.assertEqual(cases[0].sla_days, 1)
        self.assertEqual(cases[1].sla_days, 0)
        self.assertEqual(cases[2].sla_days, 0)

    @tag("987")
    def test_sla_ignores_previously_finalised_cases(self):
        application = self.create_draft_standard_application(self.organisation)
        case = self.submit_application(application)
        case.last_closed_at = timezone.now()
        _set_case_time(case, self.hour_before_cutoff)

        results = update_cases_sla.now()
        case.refresh_from_db()

        self.assertEqual(results, 0)
        self.assertEqual(case.sla_days, 0)

    @tag("987")
    def test_sla_does_not_apply_sla_twice_in_one_day(self):
        application = self.create_draft_standard_application(self.organisation)
        case = self.submit_application(application)
        case.sla_updated_at = timezone.now()
        _set_case_time(case, self.hour_before_cutoff)

        results = update_cases_sla.now()
        case.refresh_from_db()

        self.assertEqual(results, 0)
        self.assertEqual(case.sla_days, 0)

    # OPEN ECJU QUERY CUTOFF TESTS

    @tag("987")
    def test_unanswered_ecju_query_opened_before_cutoff_today_excluded(self):
        case = self.create_standard_application_case(self.organisation)
        _set_case_time(case, self.hour_before_cutoff)
        query = self.create_ecju_query(case)
        _set_case_time(query, self.hour_before_cutoff)

        results = update_cases_sla.now()

        self.assertEqual(results, 0)
        self.assertEqual(case.sla_days, 0)

    @tag("987")
    def test_unanswered_ecju_query_opened_yesterday_before_cutoff_excluded(self):
        case = self.create_standard_application_case(self.organisation)
        _set_case_time(case, self.hour_before_cutoff)
        query = self.create_ecju_query(case)
        _set_case_time(query, self.hour_before_cutoff, date=yesterday())

        results = update_cases_sla.now()

        self.assertEqual(results, 0)
        self.assertEqual(case.sla_days, 0)

    @tag("987")
    def test_unanswered_ecju_query_opened_yesterday_after_cutoff_excluded(self):
        case = self.create_standard_application_case(self.organisation)
        _set_case_time(case, self.hour_before_cutoff)
        query = self.create_ecju_query(case)
        _set_case_time(query, self.hour_after_cutoff, date=yesterday())

        results = update_cases_sla.now()

        self.assertEqual(results, 0)
        self.assertEqual(case.sla_days, 0)

    @tag("987")
    def test_sla_with_unanswered_ecju_query_opened_today_after_cutoff_included(self):
        case = self.create_standard_application_case(self.organisation)
        _set_case_time(case, self.hour_before_cutoff)
        query = self.create_ecju_query(case)
        _set_case_time(query, self.hour_after_cutoff)

        results = update_cases_sla.now()

        self.assertEqual(results, 1)
        self.assertEqual(case.sla_days, 1)

    # CLOSED ECJU QUERY CUTOFF TESTS
    @tag("987")
    def test_sla_answered_today_before_cutoff_excluded(self):
        case = self.create_standard_application_case(self.organisation)
        _set_case_time(case, self.hour_before_cutoff)
        query = self.create_ecju_query(case)
        _set_case_time(query, self.hour_before_cutoff, date=yesterday(yesterday()))
        _set_response_time(query, self.hour_before_cutoff)

        results = update_cases_sla.now()

        self.assertEqual(results, 0)
        self.assertEqual(case.sla_days, 0)

    @tag("987")
    def test_sla_answered_today_after_cutoff_excluded(self):
        case = self.create_standard_application_case(self.organisation)
        _set_case_time(case, self.hour_before_cutoff)
        query = self.create_ecju_query(case)
        _set_case_time(query, self.hour_before_cutoff, date=yesterday(yesterday()))
        _set_response_time(query, self.hour_after_cutoff)

        results = update_cases_sla.now()

        self.assertEqual(results, 0)
        self.assertEqual(case.sla_days, 0)

    @tag("987")
    def test_sla_answered_yesterday_before_cutoff_included(self):
        case = self.create_standard_application_case(self.organisation)
        _set_case_time(case, self.hour_before_cutoff)
        query = self.create_ecju_query(case)
        _set_case_time(query, self.hour_before_cutoff, date=yesterday(yesterday()))
        _set_response_time(query, self.hour_before_cutoff, date=yesterday())

        results = update_cases_sla.now()

        self.assertEqual(results, 1)
        self.assertEqual(case.sla_days, 1)

    @tag("987")
    def test_sla_answered_yesterday_after_cutoff_excluded(self):
        case = self.create_standard_application_case(self.organisation)
        _set_case_time(case, self.hour_before_cutoff)
        query = self.create_ecju_query(case)
        _set_case_time(query, self.hour_before_cutoff, date=yesterday(yesterday()))
        _set_response_time(query, self.hour_after_cutoff, date=yesterday())

        results = update_cases_sla.now()

        self.assertEqual(results, 0)
        self.assertEqual(case.sla_days, 0)


class WorkingDayTests(DataTestClient):
    @mock.patch("cases.sla.is_weekend")
    @mock.patch("cases.sla.is_bank_holiday")
    def test_weekends_ignored(self, weekend_func, bank_holiday_func):
        weekend_func.return_value = True
        bank_holiday_func.return_value = False

        result = update_cases_sla.now()

        self.assertFalse(result)

    @mock.patch("cases.sla.is_weekend")
    @mock.patch("cases.sla.is_bank_holiday")
    def test_bank_holidays_ignored(self, weekend_func, bank_holiday_func):
        weekend_func.return_value = False
        bank_holiday_func.return_value = True

        result = update_cases_sla.now()

        self.assertFalse(result)

    @mock.patch("cases.sla.is_weekend")
    @mock.patch("cases.sla.is_bank_holiday")
    def test_bank_holiday_weekend_ignored(self, weekend_func, bank_holiday_func):
        weekend_func.return_value = False
        bank_holiday_func.return_value = False

        result = update_cases_sla.now()

        # Expecting update_cases_sla to be ran, but no cases found
        self.assertEqual(result, 0)

    @parameterized.expand(
        [
            (date(2020, 2, 10), False),
            (date(2020, 2, 11), False),
            (date(2020, 2, 12), False),
            (date(2020, 2, 13), False),
            (date(2020, 2, 14), False),
            (date(2020, 2, 15), True),
            (date(2020, 2, 16), True),
        ]
    )
    def test_is_weekend(self, test_date, expected_result):
        result = is_weekend(test_date)

        self.assertEqual(result, expected_result)

    def test_is_bank_holiday(self):
        # Assumes Christmas is a bank holiday
        test_date = date(date.today().year, 12, 25)

        result = is_bank_holiday(test_date)

        self.assertTrue(result)
