from __future__ import division
import logging
from datetime import datetime, time
import requests

from background_task import background
from django.utils.timezone import now, make_aware

from cases.enums import CaseTypeSubTypeEnum
from cases.models import Case

SLA_UPDATE_TASK_TIME = time(0, 0, 0)
SLA_UPDATE_CUTOFF_TIME = time(18, 0, 0)
BANK_HOLIDAY_API = "https://www.gov.uk/bank-holidays.json"
BACKUP_FILE_NAME = "bank-holidays.csv"

STANDARD_APPLICATION_TARGET = 20
OPEN_APPLICATION_TARGET = 60
MOD_CLEARANCE_TARGET = 30


def calculate_sla_percentage(days, remaining_days):
    if remaining_days is not None:
        if remaining_days <= 0:
            return 1
        else:
            return days / (remaining_days + days)
    else:
        # SLA Not applicable for queries
        return 0


def get_application_target_sla(type):
    if type == CaseTypeSubTypeEnum.STANDARD:
        return STANDARD_APPLICATION_TARGET
    elif type == CaseTypeSubTypeEnum.OPEN:
        return OPEN_APPLICATION_TARGET
    elif type in [CaseTypeSubTypeEnum.EXHIBITION, CaseTypeSubTypeEnum.F680, CaseTypeSubTypeEnum.GIFTING]:
        return MOD_CLEARANCE_TARGET
    else:
        # TODO Update for HMRC queries in story LT-1097
        return STANDARD_APPLICATION_TARGET


def is_weekend(date):
    # Weekdays are 0 indexed so Saturday is 5 and Sunday is 6
    return date.weekday() > 4


def get_bank_holidays():
    """
    Uses the GOV bank holidays API.
    If it can connect to the API, it extracts the list of bank holidays,
    saves a backup of this list as a CSV and returns the list.
    If it cannot connect to the service it will use the CSV backup and returns the list.
    """
    data = []
    r = requests.get(BANK_HOLIDAY_API)
    if r.status_code != 200:
        logging.warning("Cannot connect to the GOV Bank Holiday API. Using local backup")
        try:
            with open(BACKUP_FILE_NAME, "r") as backup_file:
                data = backup_file.read().split(",")
        except FileNotFoundError:
            logging.error(f"No local bank holiday backup found; {BACKUP_FILE_NAME}")
    else:
        try:
            dates = r.json()["england-and-wales"]["events"]
            data = [event["date"] for event in dates]
            with open(BACKUP_FILE_NAME, "w") as backup_file:
                backup_file.write(",".join(data))
            logging.info("Fetched GOV Bank Holiday list successfully")
        except Exception as e:  # noqa
            logging.error(e)

    return data


def is_bank_holiday(date):
    formatted_date = date.strftime("%Y-%m-%d")
    return formatted_date in get_bank_holidays()


@background(schedule=make_aware(datetime.combine(now(), SLA_UPDATE_TASK_TIME)))
def update_cases_sla():
    """
    Updates all applicable cases SLA.
    Runs as a background task daily at a given time.
    Doesn't run on non-working days (bank-holidays & weekends)
    :return: Whether or not SLA updating was ran
    """

    logging.info("SLA Update Started")
    date = now()
    if not is_bank_holiday(date) and not is_weekend(date):
        # Get cases submitted before the cutoff time today, where they have never been closed
        # and where the cases SLA haven't been updated today (to avoid running twice in a single day)
        try:
            cases = Case.objects.filter(
                submitted_at__lt=make_aware(datetime.combine(date, SLA_UPDATE_CUTOFF_TIME)), last_closed_at__isnull=True
            ).exclude(sla_updated_at__day=date.day)
            for case in cases:
                case.sla_days += 1
                case.sla_remaining_days -= 1
                case.sla_updated_at = date
                case.save()
            logging.info(f"SLA Update Successful: {len(cases)} cases updated")
            return True
        except Exception as e:  # noqa
            logging.error(e)
            return False

    logging.info("SLA Update Ignored: Non-working day")
    return False
