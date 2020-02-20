from datetime import date, time, datetime
from unittest import mock

from parameterized import parameterized

from cases.enums import CaseTypeEnum
from cases.sla import (
    update_cases_sla,
    is_weekend,
    is_bank_holiday,
    STANDARD_APPLICATION_TARGET,
    OPEN_APPLICATION_TARGET,
    MOD_CLEARANCE_TARGET,
)
from test_helpers.clients import DataTestClient


class SlaTests(DataTestClient):
    def test_sla_update_standard_application(self):
        application = self.create_draft_standard_application(self.organisation)
        case = self.submit_application(application)
        case.submitted_at = datetime.combine(datetime.now(), time(12, 0, 0))

        update_cases_sla.now()
        case.refresh_from_db()

        self.assertEqual(case.sla_days, 1)
        self.assertEqual(case.sla_remaining_days, STANDARD_APPLICATION_TARGET - 1)

    def test_sla_update_open_application(self):
        application = self.create_open_application(self.organisation)
        case = self.submit_application(application)
        case.submitted_at = datetime.combine(datetime.now(), time(12, 0, 0))

        update_cases_sla.now()
        case.refresh_from_db()

        self.assertEqual(case.sla_days, 1)
        self.assertEqual(case.sla_remaining_days, OPEN_APPLICATION_TARGET - 1)

    def test_sla_update_mod_application(self):
        application = self.create_mod_clearance_application(self.organisation, CaseTypeEnum.F680)
        case = self.submit_application(application)
        case.submitted_at = datetime.combine(datetime.now(), time(12, 0, 0))

        update_cases_sla.now()
        case.refresh_from_db()

        self.assertEqual(case.sla_days, 1)
        self.assertEqual(case.sla_remaining_days, MOD_CLEARANCE_TARGET - 1)


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

        self.assertTrue(result)

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
