from django.utils.datetime_safe import date
from parameterized import parameterized

from common.dates import is_weekend, is_bank_holiday, number_of_days_since
from test_helpers.clients import DataTestClient


class DatesTests(DataTestClient):
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

    @parameterized.expand(
        [
            (date(2020, 2, 10), 1, 1),
            (date(2020, 2, 11), 2, 2),
            (date(2020, 2, 12), 3, 3),
            (date(2020, 2, 13), 4, 4),
            (date(2020, 2, 14), 5, 5),
            (date(2020, 2, 15), 6, 9),
            (date(2020, 2, 16), 7, 11),
        ]
    )
    def test_num_working_days_since(self, test_date, num_working_days, expected_result):
        result = number_of_days_since(test_date, num_working_days)

        self.assertEqual(result, expected_result)
