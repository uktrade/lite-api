import logging
from datetime import timedelta

import requests
from rest_framework import status

BANK_HOLIDAY_API = "https://www.gov.uk/bank-holidays.json"
BACKUP_FILE_NAME = "bank-holidays.csv"
LOG_PREFIX = "update_cases_sla background task:"

SECONDS_IN_DAY = 86400
SECONDS_IN_HOUR = 3600
SECONDS_IN_MINUTE = 60


def get_time_in_seconds_from_datetime(datetime):
    return (datetime.hour * SECONDS_IN_HOUR) + (datetime.minute * SECONDS_IN_MINUTE) + datetime.second


def is_working_day(date):
    return not is_weekend(date) and not is_bank_holiday(date)


def is_weekend(date):
    # Weekdays are 0 indexed so Saturday is 5 and Sunday is 6
    return date.weekday() > 4


def working_days_in_range(start_date, end_date):
    dates_in_range = [start_date + timedelta(n) for n in range((end_date - start_date).days)]
    return len([date for date in dates_in_range if not is_bank_holiday(date) or not is_weekend(date)])


def working_hours_in_range(start_date, end_date):
    """
    Use seconds to evaluate accurately how many hours have elapsed:
    start_date = 2020-04-01 00:59:59
    end_date = 2020-04-01 01:00:00
    end_date.hour - start_date.hour would result with 1hr if minutes and seconds were ignored
    """
    seconds_count = (end_date - start_date).total_seconds()

    if not is_working_day(start_date) and start_date.date() == end_date.date():
        return 0

    # If start_date is a non-working day, subtract the total seconds that were remaining on that day
    if not is_working_day(start_date):
        seconds_count -= SECONDS_IN_DAY - get_time_in_seconds_from_datetime(start_date)

    # If end_date is a non-working day, subtract the total seconds that occurred on that day
    if not is_working_day(end_date):
        seconds_count -= get_time_in_seconds_from_datetime(end_date)

    elapsed_days = end_date.day - start_date.day

    # Subtract 24 hours for every non-working day that occurred between (but not including) end_date and start_date
    for elapsed_day in range(1, elapsed_days):
        date = start_date + timedelta(days=elapsed_day)
        if not is_working_day(date):
            seconds_count -= SECONDS_IN_DAY

    # Divide by number of seconds in an hour and cast to an int to floor value with no decimal points
    return int(seconds_count // SECONDS_IN_HOUR)


def get_backup_bank_holidays():
    try:
        with open(BACKUP_FILE_NAME, "r") as backup_file:
            return backup_file.read().split(",")
    except FileNotFoundError:
        logging.error(f"{LOG_PREFIX} No local bank holiday backup found; {BACKUP_FILE_NAME}")
        return []


def get_bank_holidays(call_api=True, data=[]):  # noqa
    """
    :param data: mutable default for cache behaviour


    Uses the GOV bank holidays API.
    If it can connect to the API, it extracts the list of bank holidays,
    saves a backup of this list as a CSV and returns the list.
    If it cannot connect to the service it will use the CSV backup and returns the list.
    """
    if data and isinstance(data, list):
        return data

    if not call_api:
        return get_backup_bank_holidays()

    r = requests.get(BANK_HOLIDAY_API)
    if r.status_code != status.HTTP_200_OK:
        logging.warning(
            f"{LOG_PREFIX} Cannot connect to the GOV Bank Holiday API ({BANK_HOLIDAY_API}). Using local backup"
        )
        return get_backup_bank_holidays()
    else:
        try:
            dates = r.json()["england-and-wales"]["events"]
            for event in dates:
                data.append(event["date"])
            with open(BACKUP_FILE_NAME, "w") as backup_file:
                backup_file.write(",".join(data))
            logging.info(f"{LOG_PREFIX} Fetched GOV Bank Holiday list successfully")
        except Exception as e:  # noqa
            logging.error(e)

    return data


def is_bank_holiday(date, call_api=True):
    formatted_date = date.strftime("%Y-%m-%d")
    return formatted_date in get_bank_holidays(call_api)


def number_of_days_since(date, num_working_days):
    """
    Given a date, return the amount of days since then
    including the number of working days
    For example, given Wednesday and 5 working days, this
    function will return 7 (due to weekends)
    """
    days = 0
    while num_working_days > 0:
        days += 1
        if is_bank_holiday(date) or is_weekend(date):
            date = date - timedelta(days=1)
            continue
        num_working_days -= 1
        date = date - timedelta(days=1)

    return days
