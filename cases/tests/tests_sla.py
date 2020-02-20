from datetime import date, time
from unittest import mock

from parameterized import parameterized

from cases.sla import update_cases_sla, is_weekend, is_bank_holiday
from test_helpers.clients import DataTestClient


class WorkingDayTests(DataTestClient):
    @mock.patch("cases.sla.is_weekend")
    @mock.patch("cases.sla.is_bank_holiday")
    def test_weekends_ignored(self, is_weekend, is_bank_holiday):
        is_weekend.return_value = True
        is_bank_holiday.return_value = False

        result = update_cases_sla.now()

        self.assertFalse(result)

    @mock.patch("cases.sla.is_weekend")
    @mock.patch("cases.sla.is_bank_holiday")
    def test_bank_holidays_ignored(self, is_weekend, is_bank_holiday):
        is_weekend.return_value = False
        is_bank_holiday.return_value = True

        result = update_cases_sla.now()

        self.assertFalse(result)

    @mock.patch("cases.sla.is_weekend")
    @mock.patch("cases.sla.is_bank_holiday")
    def test_bank_holiday_weekend_ignored(self, is_weekend, is_bank_holiday):
        is_weekend.return_value = False
        is_bank_holiday.return_value = False

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
