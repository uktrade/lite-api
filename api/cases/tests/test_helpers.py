# TODO; test notify_ecju_query in total isolation

import datetime
from parameterized import parameterized

from api.cases.helpers import working_days_in_range


@parameterized.expand(
    [
        (
            {
                "year": 2022,
                "month": 11,
                "day": 30,
                "hour": 9,
                "minute": 50,
                "tzinfo": datetime.timezone.utc,
            },
            365,
            252,
        ),
        (
            {
                "year": 2023,
                "month": 12,
                "day": 15,
                "hour": 13,
                "minute": 37,
                "tzinfo": datetime.timezone.utc,
            },
            30,
            18,
        ),
        ({"year": 2024, "month": 1, "day": 22, "hour": 15, "minute": 40, "tzinfo": datetime.timezone.utc}, 7, 5),
        (
            {
                "year": 2024,
                "month": 1,
                "day": 28,
                "hour": 12,
                "minute": 6,
                "tzinfo": datetime.timezone.utc,
            },
            1,
            0,
        ),
    ],
)
def test_working_days_in_range(created_at_datetime_kwargs, calendar_days, expected_working_days):
    start_date = datetime.datetime(**created_at_datetime_kwargs)
    end_date = start_date + datetime.timedelta(days=calendar_days)

    assert working_days_in_range(start_date, end_date) == expected_working_days
