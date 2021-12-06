from django.utils.datetime_safe import date, datetime
from parameterized import parameterized

import requests_mock

from api.common.dates import is_weekend, is_bank_holiday, number_of_days_since, working_hours_in_range, BANK_HOLIDAY_API
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
        data = {
            "england-and-wales": {
                "division": "england-and-wales",
                "events": [
                    {"title": "New Year’s Day", "date": "2021-01-01", "notes": "", "bunting": True},
                    {"title": "Good Friday", "date": "2016-03-25", "notes": "", "bunting": False},
                ],
            }
        }
        with requests_mock.Mocker() as m:
            m.get(BANK_HOLIDAY_API, json=data)

            test_date = date(2021, 1, 1)
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

    @parameterized.expand(
        [
            # Start day = Wednesday(00:00), End day = Friday(00:00), Expected hours = 48
            (datetime(2020, 4, 1), datetime(2020, 4, 3), 48),
            # Start day = Wednesday(14:00), End day = Friday(14:00), Expected hours = 48
            (datetime(2020, 4, 1, 14), datetime(2020, 4, 3, 14), 48),
            # Start day = Wednesday(14:00), End day = Friday(00:00), Expected hours = 34
            (datetime(2020, 4, 1, 14), datetime(2020, 4, 3), 34),
            # Start day = Wednesday(00:00), End day = Friday(14:00), Expected hours = 62
            (datetime(2020, 4, 1), datetime(2020, 4, 3, 14), 62),
            # Start day = Wednesday(00:00), End day = Wednesday(00:59:59), Expected hours = 0
            (datetime(2020, 4, 1), datetime(2020, 4, 1, 0, 59, 59), 0),
            # Start day = Wednesday(00:00), End day = Wednesday(01:00), Expected hours = 1
            (datetime(2020, 4, 1), datetime(2020, 4, 1, 1), 1),
        ]
    )
    def test_num_working_hours_over_working_days(self, start_date, end_date, expected_result):
        result = working_hours_in_range(start_date, end_date)
        self.assertEqual(result, expected_result)

    @parameterized.expand(
        [
            # Start day = Friday(00:00), End day = Sunday(00:00), Expected hours = 24
            (datetime(2020, 4, 3), datetime(2020, 4, 5), 24),
            # Start day = Friday(00:00), End day = Monday(00:00), Expected hours = 24
            (datetime(2020, 4, 3), datetime(2020, 4, 6), 24),
            # Start day = Friday(00:00), End day = Monday(01:00), Expected hours = 25
            (datetime(2020, 4, 3), datetime(2020, 4, 6, 1), 25),
            # Start day = Friday(00:00), End day = Tuesday(01:00), Expected hours = 49
            (datetime(2020, 4, 3), datetime(2020, 4, 7, 1), 49),
            # Start day = Saturday(00:00), End day = Sunday(09:45:52), Expected hours = 0
            (datetime(2020, 4, 4), datetime(2020, 4, 5, 9, 45, 52), 0),
        ]
    )
    def test_num_working_hours_over_weekends(self, start_date, end_date, expected_result):
        result = working_hours_in_range(start_date, end_date)
        self.assertEqual(result, expected_result)

    @parameterized.expand(
        [
            # Start day = Good Friday(00:00), End day = Day after Easter Monday(00:00), Expected hours = 0
            (datetime(2020, 4, 10), datetime(2020, 4, 14), 0),
            # Start day = Good Friday(00:00), End day = Day after Easter Monday(01:30), Expected hours = 1
            (datetime(2020, 4, 10), datetime(2020, 4, 14, 1, 30), 1),
            # Start day = Day before Good Friday(00:00), End day = Day after Easter Monday(00:00), Expected hours = 24
            (datetime(2020, 4, 9), datetime(2020, 4, 14), 24),
            # Start day = Day before Good Friday(12:00), End day = Day after Easter Monday(00:00), Expected hours = 12
            (datetime(2020, 4, 9, 12), datetime(2020, 4, 14), 12),
            # Start day = Day before Good Friday(12:00), End day = Day after Easter Monday(15:00), Expected hours = 27
            (datetime(2020, 4, 9, 12), datetime(2020, 4, 14, 15), 27),
        ]
    )
    def test_num_working_hours_over_bank_holidays(self, start_date, end_date, expected_result):
        result = working_hours_in_range(start_date, end_date)
        self.assertEqual(result, expected_result)

    def test_num_working_hours_over_working_days_weekends_bank_holidays(self):
        start_date = datetime(2020, 4, 9, 12)  # Day before Good Friday(12:00)
        end_date = datetime(2020, 4, 30, 13, 22, 5)  # Three weeks later(13:22:05)
        expected_result = 313  # 12hrs in start_date + 13hrs in end_date + (12 working days * 24hrs)

        result = working_hours_in_range(start_date, end_date)
        self.assertEqual(result, expected_result)
