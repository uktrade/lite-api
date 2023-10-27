import pytest
from django.utils.datetime_safe import date, datetime
from parameterized import parameterized

import requests_mock

from api.common.dates import is_weekend, is_bank_holiday, number_of_days_since, working_hours_in_range, BANK_HOLIDAY_API
from test_helpers.clients import DataTestClient


@pytest.fixture(autouse=True)
def mock_bank_holidays_api(requests_mock):
    data = {
        "england-and-wales": {
            "division": "england-and-wales",
            "events": [
                {"bunting": True, "date": "2018-01-01", "notes": "", "title": "New Year’s Day"},
                {"bunting": False, "date": "2018-03-30", "notes": "", "title": "Good Friday"},
                {"bunting": True, "date": "2018-04-02", "notes": "", "title": "Easter Monday"},
                {"bunting": True, "date": "2018-05-07", "notes": "", "title": "Early May bank holiday"},
                {"bunting": True, "date": "2018-05-28", "notes": "", "title": "Spring bank holiday"},
                {"bunting": True, "date": "2018-08-27", "notes": "", "title": "Summer bank holiday"},
                {"bunting": True, "date": "2018-12-25", "notes": "", "title": "Christmas Day"},
                {"bunting": True, "date": "2018-12-26", "notes": "", "title": "Boxing Day"},
                {"bunting": True, "date": "2019-01-01", "notes": "", "title": "New Year’s Day"},
                {"bunting": False, "date": "2019-04-19", "notes": "", "title": "Good Friday"},
                {"bunting": True, "date": "2019-04-22", "notes": "", "title": "Easter Monday"},
                {"bunting": True, "date": "2019-05-06", "notes": "", "title": "Early May bank holiday"},
                {"bunting": True, "date": "2019-05-27", "notes": "", "title": "Spring bank holiday"},
                {"bunting": True, "date": "2019-08-26", "notes": "", "title": "Summer bank holiday"},
                {"bunting": True, "date": "2019-12-25", "notes": "", "title": "Christmas Day"},
                {"bunting": True, "date": "2019-12-26", "notes": "", "title": "Boxing Day"},
                {"bunting": True, "date": "2020-01-01", "notes": "", "title": "New Year’s Day"},
                {"bunting": False, "date": "2020-04-10", "notes": "", "title": "Good Friday"},
                {"bunting": False, "date": "2020-04-13", "notes": "", "title": "Easter Monday"},
                {"bunting": True, "date": "2020-05-08", "notes": "", "title": "Early May bank holiday (VE day)"},
                {"bunting": True, "date": "2020-05-25", "notes": "", "title": "Spring bank holiday"},
                {"bunting": True, "date": "2020-08-31", "notes": "", "title": "Summer bank holiday"},
                {"bunting": True, "date": "2020-12-25", "notes": "", "title": "Christmas Day"},
                {"bunting": True, "date": "2020-12-28", "notes": "Substitute day", "title": "Boxing Day"},
                {"bunting": True, "date": "2021-01-01", "notes": "", "title": "New Year’s Day"},
                {"bunting": False, "date": "2021-04-02", "notes": "", "title": "Good Friday"},
                {"bunting": True, "date": "2021-04-05", "notes": "", "title": "Easter Monday"},
                {"bunting": True, "date": "2021-05-03", "notes": "", "title": "Early May bank holiday"},
                {"bunting": True, "date": "2021-05-31", "notes": "", "title": "Spring bank holiday"},
                {"bunting": True, "date": "2021-08-30", "notes": "", "title": "Summer bank holiday"},
                {"bunting": True, "date": "2021-12-27", "notes": "Substitute day", "title": "Christmas Day"},
                {"bunting": True, "date": "2021-12-28", "notes": "Substitute day", "title": "Boxing Day"},
                {"bunting": True, "date": "2022-01-03", "notes": "Substitute day", "title": "New Year’s Day"},
                {"bunting": False, "date": "2022-04-15", "notes": "", "title": "Good Friday"},
                {"bunting": True, "date": "2022-04-18", "notes": "", "title": "Easter Monday"},
                {"bunting": True, "date": "2022-05-02", "notes": "", "title": "Early May bank holiday"},
                {"bunting": True, "date": "2022-06-02", "notes": "", "title": "Spring bank holiday"},
                {"bunting": True, "date": "2022-06-03", "notes": "", "title": "Platinum Jubilee bank holiday"},
                {"bunting": True, "date": "2022-08-29", "notes": "", "title": "Summer bank holiday"},
                {
                    "bunting": False,
                    "date": "2022-09-19",
                    "notes": "",
                    "title": "Bank Holiday for the State " "Funeral of Queen Elizabeth II",
                },
                {"bunting": True, "date": "2022-12-26", "notes": "", "title": "Boxing Day"},
                {"bunting": True, "date": "2022-12-27", "notes": "Substitute day", "title": "Christmas Day"},
                {"bunting": True, "date": "2023-01-02", "notes": "Substitute day", "title": "New Year’s Day"},
                {"bunting": False, "date": "2023-04-07", "notes": "", "title": "Good Friday"},
                {"bunting": True, "date": "2023-04-10", "notes": "", "title": "Easter Monday"},
                {"bunting": True, "date": "2023-05-01", "notes": "", "title": "Early May bank holiday"},
                {
                    "bunting": True,
                    "date": "2023-05-08",
                    "notes": "",
                    "title": "Bank holiday for the coronation " "of King Charles III",
                },
                {"bunting": True, "date": "2023-05-29", "notes": "", "title": "Spring bank holiday"},
                {"bunting": True, "date": "2023-08-28", "notes": "", "title": "Summer bank holiday"},
                {"bunting": True, "date": "2023-12-25", "notes": "", "title": "Christmas Day"},
                {"bunting": True, "date": "2023-12-26", "notes": "", "title": "Boxing Day"},
                {"bunting": True, "date": "2024-01-01", "notes": "", "title": "New Year’s Day"},
                {"bunting": False, "date": "2024-03-29", "notes": "", "title": "Good Friday"},
                {"bunting": True, "date": "2024-04-01", "notes": "", "title": "Easter Monday"},
                {"bunting": True, "date": "2024-05-06", "notes": "", "title": "Early May bank holiday"},
                {"bunting": True, "date": "2024-05-27", "notes": "", "title": "Spring bank holiday"},
                {"bunting": True, "date": "2024-08-26", "notes": "", "title": "Summer bank holiday"},
                {"bunting": True, "date": "2024-12-25", "notes": "", "title": "Christmas Day"},
                {"bunting": True, "date": "2024-12-26", "notes": "", "title": "Boxing Day"},
                {"bunting": True, "date": "2025-01-01", "notes": "", "title": "New Year’s Day"},
                {"bunting": False, "date": "2025-04-18", "notes": "", "title": "Good Friday"},
                {"bunting": True, "date": "2025-04-21", "notes": "", "title": "Easter Monday"},
                {"bunting": True, "date": "2025-05-05", "notes": "", "title": "Early May bank holiday"},
                {"bunting": True, "date": "2025-05-26", "notes": "", "title": "Spring bank holiday"},
                {"bunting": True, "date": "2025-08-25", "notes": "", "title": "Summer bank holiday"},
                {"bunting": True, "date": "2025-12-25", "notes": "", "title": "Christmas Day"},
                {"bunting": True, "date": "2025-12-26", "notes": "", "title": "Boxing Day"},
            ],
        },
        "northern-ireland": {
            "division": "northern-ireland",
            "events": [
                {"bunting": True, "date": "2018-01-01", "notes": "", "title": "New Year’s Day"},
                {"bunting": True, "date": "2018-03-19", "notes": "Substitute day", "title": "St Patrick’s Day"},
                {"bunting": False, "date": "2018-03-30", "notes": "", "title": "Good Friday"},
                {"bunting": True, "date": "2018-04-02", "notes": "", "title": "Easter Monday"},
                {"bunting": True, "date": "2018-05-07", "notes": "", "title": "Early May bank holiday"},
                {"bunting": True, "date": "2018-05-28", "notes": "", "title": "Spring bank holiday"},
                {
                    "bunting": False,
                    "date": "2018-07-12",
                    "notes": "",
                    "title": "Battle of the Boyne (Orangemen’s " "Day)",
                },
                {"bunting": True, "date": "2018-08-27", "notes": "", "title": "Summer bank holiday"},
                {"bunting": True, "date": "2018-12-25", "notes": "", "title": "Christmas Day"},
                {"bunting": True, "date": "2018-12-26", "notes": "", "title": "Boxing Day"},
                {"bunting": True, "date": "2019-01-01", "notes": "", "title": "New Year’s Day"},
                {"bunting": True, "date": "2019-03-18", "notes": "Substitute day", "title": "St Patrick’s Day"},
                {"bunting": False, "date": "2019-04-19", "notes": "", "title": "Good Friday"},
                {"bunting": True, "date": "2019-04-22", "notes": "", "title": "Easter Monday"},
                {"bunting": True, "date": "2019-05-06", "notes": "", "title": "Early May bank holiday"},
                {"bunting": True, "date": "2019-05-27", "notes": "", "title": "Spring bank holiday"},
                {
                    "bunting": False,
                    "date": "2019-07-12",
                    "notes": "",
                    "title": "Battle of the Boyne (Orangemen’s " "Day)",
                },
                {"bunting": True, "date": "2019-08-26", "notes": "", "title": "Summer bank holiday"},
                {"bunting": True, "date": "2019-12-25", "notes": "", "title": "Christmas Day"},
                {"bunting": True, "date": "2019-12-26", "notes": "", "title": "Boxing Day"},
                {"bunting": True, "date": "2020-01-01", "notes": "", "title": "New Year’s Day"},
                {"bunting": True, "date": "2020-03-17", "notes": "", "title": "St Patrick’s Day"},
                {"bunting": False, "date": "2020-04-10", "notes": "", "title": "Good Friday"},
                {"bunting": False, "date": "2020-04-13", "notes": "", "title": "Easter Monday"},
                {"bunting": True, "date": "2020-05-08", "notes": "", "title": "Early May bank holiday (VE day)"},
                {"bunting": True, "date": "2020-05-25", "notes": "", "title": "Spring bank holiday"},
                {
                    "bunting": False,
                    "date": "2020-07-13",
                    "notes": "Substitute day",
                    "title": "Battle of the Boyne (Orangemen’s " "Day)",
                },
                {"bunting": True, "date": "2020-08-31", "notes": "", "title": "Summer bank holiday"},
                {"bunting": True, "date": "2020-12-25", "notes": "", "title": "Christmas Day"},
                {"bunting": True, "date": "2020-12-28", "notes": "Substitute day", "title": "Boxing Day"},
                {"bunting": True, "date": "2021-01-01", "notes": "", "title": "New Year’s Day"},
                {"bunting": True, "date": "2021-03-17", "notes": "", "title": "St Patrick’s Day"},
                {"bunting": False, "date": "2021-04-02", "notes": "", "title": "Good Friday"},
                {"bunting": True, "date": "2021-04-05", "notes": "", "title": "Easter Monday"},
                {"bunting": True, "date": "2021-05-03", "notes": "", "title": "Early May bank holiday"},
                {"bunting": True, "date": "2021-05-31", "notes": "", "title": "Spring bank holiday"},
                {
                    "bunting": False,
                    "date": "2021-07-12",
                    "notes": "",
                    "title": "Battle of the Boyne (Orangemen’s " "Day)",
                },
                {"bunting": True, "date": "2021-08-30", "notes": "", "title": "Summer bank holiday"},
                {"bunting": True, "date": "2021-12-27", "notes": "Substitute day", "title": "Christmas Day"},
                {"bunting": True, "date": "2021-12-28", "notes": "Substitute day", "title": "Boxing Day"},
                {"bunting": True, "date": "2022-01-03", "notes": "Substitute day", "title": "New Year’s Day"},
                {"bunting": True, "date": "2022-03-17", "notes": "", "title": "St Patrick’s Day"},
                {"bunting": False, "date": "2022-04-15", "notes": "", "title": "Good Friday"},
                {"bunting": True, "date": "2022-04-18", "notes": "", "title": "Easter Monday"},
                {"bunting": True, "date": "2022-05-02", "notes": "", "title": "Early May bank holiday"},
                {"bunting": True, "date": "2022-06-02", "notes": "", "title": "Spring bank holiday"},
                {"bunting": True, "date": "2022-06-03", "notes": "", "title": "Platinum Jubilee bank holiday"},
                {
                    "bunting": False,
                    "date": "2022-07-12",
                    "notes": "",
                    "title": "Battle of the Boyne (Orangemen’s " "Day)",
                },
                {"bunting": True, "date": "2022-08-29", "notes": "", "title": "Summer bank holiday"},
                {
                    "bunting": False,
                    "date": "2022-09-19",
                    "notes": "",
                    "title": "Bank Holiday for the State Funeral " "of Queen Elizabeth II",
                },
                {"bunting": True, "date": "2022-12-26", "notes": "", "title": "Boxing Day"},
                {"bunting": True, "date": "2022-12-27", "notes": "Substitute day", "title": "Christmas Day"},
                {"bunting": True, "date": "2023-01-02", "notes": "Substitute day", "title": "New Year’s Day"},
                {"bunting": True, "date": "2023-03-17", "notes": "", "title": "St Patrick’s Day"},
                {"bunting": False, "date": "2023-04-07", "notes": "", "title": "Good Friday"},
                {"bunting": True, "date": "2023-04-10", "notes": "", "title": "Easter Monday"},
                {"bunting": True, "date": "2023-05-01", "notes": "", "title": "Early May bank holiday"},
                {
                    "bunting": True,
                    "date": "2023-05-08",
                    "notes": "",
                    "title": "Bank holiday for the coronation of " "King Charles III",
                },
                {"bunting": True, "date": "2023-05-29", "notes": "", "title": "Spring bank holiday"},
                {
                    "bunting": False,
                    "date": "2023-07-12",
                    "notes": "",
                    "title": "Battle of the Boyne (Orangemen’s " "Day)",
                },
                {"bunting": True, "date": "2023-08-28", "notes": "", "title": "Summer bank holiday"},
                {"bunting": True, "date": "2023-12-25", "notes": "", "title": "Christmas Day"},
                {"bunting": True, "date": "2023-12-26", "notes": "", "title": "Boxing Day"},
                {"bunting": True, "date": "2024-01-01", "notes": "", "title": "New Year’s Day"},
                {"bunting": True, "date": "2024-03-18", "notes": "Substitute day", "title": "St Patrick’s Day"},
                {"bunting": False, "date": "2024-03-29", "notes": "", "title": "Good Friday"},
                {"bunting": True, "date": "2024-04-01", "notes": "", "title": "Easter Monday"},
                {"bunting": True, "date": "2024-05-06", "notes": "", "title": "Early May bank holiday"},
                {"bunting": True, "date": "2024-05-27", "notes": "", "title": "Spring bank holiday"},
                {
                    "bunting": False,
                    "date": "2024-07-12",
                    "notes": "",
                    "title": "Battle of the Boyne (Orangemen’s " "Day)",
                },
                {"bunting": True, "date": "2024-08-26", "notes": "", "title": "Summer bank holiday"},
                {"bunting": True, "date": "2024-12-25", "notes": "", "title": "Christmas Day"},
                {"bunting": True, "date": "2024-12-26", "notes": "", "title": "Boxing Day"},
                {"bunting": True, "date": "2025-01-01", "notes": "", "title": "New Year’s Day"},
                {"bunting": True, "date": "2025-03-17", "notes": "", "title": "St Patrick’s Day"},
                {"bunting": False, "date": "2025-04-18", "notes": "", "title": "Good Friday"},
                {"bunting": True, "date": "2025-04-21", "notes": "", "title": "Easter Monday"},
                {"bunting": True, "date": "2025-05-05", "notes": "", "title": "Early May bank holiday"},
                {"bunting": True, "date": "2025-05-26", "notes": "", "title": "Spring bank holiday"},
                {
                    "bunting": False,
                    "date": "2025-07-14",
                    "notes": "Substitute day",
                    "title": "Battle of the Boyne (Orangemen’s " "Day)",
                },
                {"bunting": True, "date": "2025-08-25", "notes": "", "title": "Summer bank holiday"},
                {"bunting": True, "date": "2025-12-25", "notes": "", "title": "Christmas Day"},
                {"bunting": True, "date": "2025-12-26", "notes": "", "title": "Boxing Day"},
            ],
        },
        "scotland": {
            "division": "scotland",
            "events": [
                {"bunting": True, "date": "2018-01-01", "notes": "", "title": "New Year’s Day"},
                {"bunting": True, "date": "2018-01-02", "notes": "", "title": "2nd January"},
                {"bunting": False, "date": "2018-03-30", "notes": "", "title": "Good Friday"},
                {"bunting": True, "date": "2018-05-07", "notes": "", "title": "Early May bank holiday"},
                {"bunting": True, "date": "2018-05-28", "notes": "", "title": "Spring bank holiday"},
                {"bunting": True, "date": "2018-08-06", "notes": "", "title": "Summer bank holiday"},
                {"bunting": True, "date": "2018-11-30", "notes": "", "title": "St Andrew’s Day"},
                {"bunting": True, "date": "2018-12-25", "notes": "", "title": "Christmas Day"},
                {"bunting": True, "date": "2018-12-26", "notes": "", "title": "Boxing Day"},
                {"bunting": True, "date": "2019-01-01", "notes": "", "title": "New Year’s Day"},
                {"bunting": True, "date": "2019-01-02", "notes": "", "title": "2nd January"},
                {"bunting": False, "date": "2019-04-19", "notes": "", "title": "Good Friday"},
                {"bunting": True, "date": "2019-05-06", "notes": "", "title": "Early May bank holiday"},
                {"bunting": True, "date": "2019-05-27", "notes": "", "title": "Spring bank holiday"},
                {"bunting": True, "date": "2019-08-05", "notes": "", "title": "Summer bank holiday"},
                {"bunting": True, "date": "2019-12-02", "notes": "Substitute day", "title": "St Andrew’s Day"},
                {"bunting": True, "date": "2019-12-25", "notes": "", "title": "Christmas Day"},
                {"bunting": True, "date": "2019-12-26", "notes": "", "title": "Boxing Day"},
                {"bunting": True, "date": "2020-01-01", "notes": "", "title": "New Year’s Day"},
                {"bunting": True, "date": "2020-01-02", "notes": "", "title": "2nd January"},
                {"bunting": False, "date": "2020-04-10", "notes": "", "title": "Good Friday"},
                {"bunting": True, "date": "2020-05-08", "notes": "", "title": "Early May bank holiday (VE day)"},
                {"bunting": True, "date": "2020-05-25", "notes": "", "title": "Spring bank holiday"},
                {"bunting": True, "date": "2020-08-03", "notes": "", "title": "Summer bank holiday"},
                {"bunting": True, "date": "2020-11-30", "notes": "", "title": "St Andrew’s Day"},
                {"bunting": True, "date": "2020-12-25", "notes": "", "title": "Christmas Day"},
                {"bunting": True, "date": "2020-12-28", "notes": "Substitute day", "title": "Boxing Day"},
                {"bunting": True, "date": "2021-01-01", "notes": "", "title": "New Year’s Day"},
                {"bunting": True, "date": "2021-01-04", "notes": "Substitute day", "title": "2nd January"},
                {"bunting": False, "date": "2021-04-02", "notes": "", "title": "Good Friday"},
                {"bunting": True, "date": "2021-05-03", "notes": "", "title": "Early May bank holiday"},
                {"bunting": True, "date": "2021-05-31", "notes": "", "title": "Spring bank holiday"},
                {"bunting": True, "date": "2021-08-02", "notes": "", "title": "Summer bank holiday"},
                {"bunting": True, "date": "2021-11-30", "notes": "", "title": "St Andrew’s Day"},
                {"bunting": True, "date": "2021-12-27", "notes": "Substitute day", "title": "Christmas Day"},
                {"bunting": True, "date": "2021-12-28", "notes": "Substitute day", "title": "Boxing Day"},
                {"bunting": True, "date": "2022-01-03", "notes": "Substitute day", "title": "New Year’s Day"},
                {"bunting": True, "date": "2022-01-04", "notes": "Substitute day", "title": "2nd January"},
                {"bunting": False, "date": "2022-04-15", "notes": "", "title": "Good Friday"},
                {"bunting": True, "date": "2022-05-02", "notes": "", "title": "Early May bank holiday"},
                {"bunting": True, "date": "2022-06-02", "notes": "", "title": "Spring bank holiday"},
                {"bunting": True, "date": "2022-06-03", "notes": "", "title": "Platinum Jubilee bank holiday"},
                {"bunting": True, "date": "2022-08-01", "notes": "", "title": "Summer bank holiday"},
                {
                    "bunting": False,
                    "date": "2022-09-19",
                    "notes": "",
                    "title": "Bank Holiday for the State Funeral of " "Queen Elizabeth II",
                },
                {"bunting": True, "date": "2022-11-30", "notes": "", "title": "St Andrew’s Day"},
                {"bunting": True, "date": "2022-12-26", "notes": "", "title": "Boxing Day"},
                {"bunting": True, "date": "2022-12-27", "notes": "Substitute day", "title": "Christmas Day"},
                {"bunting": True, "date": "2023-01-02", "notes": "Substitute day", "title": "New Year’s Day"},
                {"bunting": True, "date": "2023-01-03", "notes": "Substitute day", "title": "2nd January"},
                {"bunting": False, "date": "2023-04-07", "notes": "", "title": "Good Friday"},
                {"bunting": True, "date": "2023-05-01", "notes": "", "title": "Early May bank holiday"},
                {
                    "bunting": True,
                    "date": "2023-05-08",
                    "notes": "",
                    "title": "Bank holiday for the coronation of King " "Charles III",
                },
                {"bunting": True, "date": "2023-05-29", "notes": "", "title": "Spring bank holiday"},
                {"bunting": True, "date": "2023-08-07", "notes": "", "title": "Summer bank holiday"},
                {"bunting": True, "date": "2023-11-30", "notes": "", "title": "St Andrew’s Day"},
                {"bunting": True, "date": "2023-12-25", "notes": "", "title": "Christmas Day"},
                {"bunting": True, "date": "2023-12-26", "notes": "", "title": "Boxing Day"},
                {"bunting": True, "date": "2024-01-01", "notes": "", "title": "New Year’s Day"},
                {"bunting": True, "date": "2024-01-02", "notes": "", "title": "2nd January"},
                {"bunting": False, "date": "2024-03-29", "notes": "", "title": "Good Friday"},
                {"bunting": True, "date": "2024-05-06", "notes": "", "title": "Early May bank holiday"},
                {"bunting": True, "date": "2024-05-27", "notes": "", "title": "Spring bank holiday"},
                {"bunting": True, "date": "2024-08-05", "notes": "", "title": "Summer bank holiday"},
                {"bunting": True, "date": "2024-12-02", "notes": "Substitute day", "title": "St Andrew’s Day"},
                {"bunting": True, "date": "2024-12-25", "notes": "", "title": "Christmas Day"},
                {"bunting": True, "date": "2024-12-26", "notes": "", "title": "Boxing Day"},
                {"bunting": True, "date": "2025-01-01", "notes": "", "title": "New Year’s Day"},
                {"bunting": True, "date": "2025-01-02", "notes": "", "title": "2nd January"},
                {"bunting": False, "date": "2025-04-18", "notes": "", "title": "Good Friday"},
                {"bunting": True, "date": "2025-05-05", "notes": "", "title": "Early May bank holiday"},
                {"bunting": True, "date": "2025-05-26", "notes": "", "title": "Spring bank holiday"},
                {"bunting": True, "date": "2025-08-04", "notes": "", "title": "Summer bank holiday"},
                {"bunting": True, "date": "2025-12-01", "notes": "Substitute day", "title": "St Andrew’s Day"},
                {"bunting": True, "date": "2025-12-25", "notes": "", "title": "Christmas Day"},
                {"bunting": True, "date": "2025-12-26", "notes": "", "title": "Boxing Day"},
            ],
        },
    }
    requests_mock.get(BANK_HOLIDAY_API, json=data)


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
