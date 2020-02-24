from datetime import date, time
from unittest import mock

from django.utils.timezone import datetime, now
from parameterized import parameterized

from cases.enums import CaseTypeEnum
from cases.models import Case
from cases.sla import (
    update_cases_sla,
    is_weekend,
    is_bank_holiday,
    STANDARD_APPLICATION_TARGET,
    OPEN_APPLICATION_TARGET,
    MOD_CLEARANCE_TARGET,
    SLA_UPDATE_CUTOFF_TIME,
)
from test_helpers.clients import DataTestClient


class SlaTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.hour_before_cutoff = time(SLA_UPDATE_CUTOFF_TIME.hour - 1, 0, 0)
        self.hour_after_cutoff = time(SLA_UPDATE_CUTOFF_TIME.hour + 1, 0, 0)

    @staticmethod
    def _set_case_time(case, submit_time):
        case.submitted_at = datetime.combine(now(), submit_time)
        case.save()

    def test_sla_update_standard_application(self):
        application = self.create_draft_standard_application(self.organisation)
        case = self.submit_application(application)
        self._set_case_time(case, self.hour_before_cutoff)

        results = update_cases_sla.now()
        case.refresh_from_db()

        self.assertEqual(results, 1)
        self.assertEqual(case.sla_days, 1)
        self.assertEqual(case.sla_remaining_days, STANDARD_APPLICATION_TARGET - 1)

    def test_sla_update_open_application(self):
        application = self.create_open_application(self.organisation)
        case = self.submit_application(application)
        self._set_case_time(case, self.hour_before_cutoff)

        results = update_cases_sla.now()
        case.refresh_from_db()

        self.assertEqual(results, 1)
        self.assertEqual(case.sla_days, 1)
        self.assertEqual(case.sla_remaining_days, OPEN_APPLICATION_TARGET - 1)

    def test_sla_update_mod_application(self):
        application = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.F680)
        case = self.submit_application(application)
        self._set_case_time(case, self.hour_before_cutoff)

        results = update_cases_sla.now()
        case.refresh_from_db()

        self.assertEqual(results, 1)
        self.assertEqual(case.sla_days, 1)
        self.assertEqual(case.sla_remaining_days, MOD_CLEARANCE_TARGET - 1)

    def test_sla_cutoff_window(self):
        times = [
            self.hour_before_cutoff,
            SLA_UPDATE_CUTOFF_TIME,
            self.hour_after_cutoff,
        ]
        for submit_time in times:
            application = self.create_draft_standard_application(self.organisation)
            case = self.submit_application(application)
            self._set_case_time(case, submit_time)

        results = update_cases_sla.now()
        cases = Case.objects.all().order_by("submitted_at")

        self.assertEqual(results, 1)
        self.assertEqual(cases[0].sla_days, 1)
        self.assertEqual(cases[1].sla_days, 0)
        self.assertEqual(cases[2].sla_days, 0)

    def test_sla_ignores_previously_finalised_cases(self):
        application = self.create_draft_standard_application(self.organisation)
        case = self.submit_application(application)
        case.last_closed_at = now()
        self._set_case_time(case, self.hour_before_cutoff)

        results = update_cases_sla.now()
        case.refresh_from_db()

        self.assertEqual(results, 0)
        self.assertEqual(case.sla_days, 0)

    def test_sla_does_not_apply_sla_twice_in_one_day(self):
        application = self.create_draft_standard_application(self.organisation)
        case = self.submit_application(application)
        case.sla_updated_at = now()
        self._set_case_time(case, self.hour_before_cutoff)

        results = update_cases_sla.now()
        case.refresh_from_db()

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
