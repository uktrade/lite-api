import logging
from datetime import timedelta

import requests
from rest_framework import status


BANK_HOLIDAY_API = "https://www.gov.uk/bank-holidays.json"
BACKUP_FILE_NAME = "bank-holidays.csv"
LOG_PREFIX = "update_cases_sla background task:"
BANK_HOLIDAYS_CACHE = []


def is_weekend(date):
    # Weekdays are 0 indexed so Saturday is 5 and Sunday is 6
    return date.weekday() > 4


def working_days_in_range(start_date, end_date):
    dates_in_range = [start_date + timedelta(n) for n in range((end_date - start_date).days)]
    return len([date for date in dates_in_range if not is_bank_holiday(date) or not is_weekend(date)])


def get_bank_holidays(data=BANK_HOLIDAYS_CACHE):  # noqa
    """
    :param data: mutable default for cache behaviour


    Uses the GOV bank holidays API.
    If it can connect to the API, it extracts the list of bank holidays,
    saves a backup of this list as a CSV and returns the list.
    If it cannot connect to the service it will use the CSV backup and returns the list.
    """
    if data and isinstance(data, list):
        return data

    r = requests.get(BANK_HOLIDAY_API)
    if r.status_code != status.HTTP_200_OK:
        logging.warning(
            f"{LOG_PREFIX} Cannot connect to the GOV Bank Holiday API ({BANK_HOLIDAY_API}). Using local backup"
        )
        try:
            with open(BACKUP_FILE_NAME, "r") as backup_file:
                data = backup_file.read().split(",")
        except FileNotFoundError:
            logging.error(f"{LOG_PREFIX} No local bank holiday backup found; {BACKUP_FILE_NAME}")
    else:
        try:
            dates = r.json()["england-and-wales"]["events"]
            data = [event["date"] for event in dates]
            with open(BACKUP_FILE_NAME, "w") as backup_file:
                backup_file.write(",".join(data))
            logging.info(f"{LOG_PREFIX} Fetched GOV Bank Holiday list successfully")
        except Exception as e:  # noqa
            logging.error(e)

    return data


def is_bank_holiday(date):
    formatted_date = date.strftime("%Y-%m-%d")
    return formatted_date in get_bank_holidays()


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
