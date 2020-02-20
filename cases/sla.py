from datetime import datetime, time
import requests

from background_task import background

from cases.models import Case

SLA_UPDATE_TASK_TIME = time(0, 0, 0)
SLA_UPDATE_CUTOFF_TIME = time(18, 0, 0)
BANK_HOLIDAY_API = "https://www.gov.uk/bank-holidays.json"
BACKUP_FILE_NAME = "bank-holidays.csv"


def is_weekend(date):
    # Weekdays are 0 indexed so Saturday is 5 and Sunday is 6
    return date.weekday() > 4


def get_bank_holidays():
    """
    Uses the GOV bank holidays API (or a local backup if the service is unavailable).
    Returns whether the list of bank holidays
    """
    r = requests.get(BANK_HOLIDAY_API)
    if r.status_code != 200:
        with open(BACKUP_FILE_NAME, "r") as backup_file:
            return backup_file.read().split(",")
    else:
        data = r.json()["england-and-wales"]["events"]
        data = [event["date"] for event in data]
        with open(BACKUP_FILE_NAME, "w") as backup_file:
            backup_file.write(",".join(data))
        return data


def is_bank_holiday(date):
    formatted_date = date.strftime("%Y-%m-%d")
    return formatted_date in get_bank_holidays()


@background(schedule=datetime.combine(datetime.now(), SLA_UPDATE_TASK_TIME))
def update_cases_sla():
    date = datetime.now()
    if not is_bank_holiday(date) and not is_weekend(date):
        cases = Case.objects.filter(submitted_at__lt=datetime.combine(date, SLA_UPDATE_CUTOFF_TIME))
        return cases
