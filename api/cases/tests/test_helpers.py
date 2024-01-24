# TODO; test notify_ecju_query in total isolation

import datetime

from api.cases.helpers import working_days_in_range


def test_working_days_in_range():
    start_date = datetime.datetime(2023, 12, 22, 12, 30, 0, 123456)
    end_date = datetime.datetime(2024, 1, 22, 12, 30, 0, 123456)

    assert working_days_in_range(start_date, end_date) == 18
