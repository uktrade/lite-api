from datetime import datetime, time

from background_task import background

from cases.models import Case

SLA_UPDATE_TASK_TIME = time(0, 0, 0)
SLA_UPDATE_CUTOFF_TIME = time(18, 0, 0)


def is_weekend(date):
    # Weekdays are 0 indexed so Saturday is 5 and Sunday is 6
    return date.weekday() > 4


def is_bank_holiday(date):
    """
    Uses the GOV bank holidays API (or a cached version if the service is unavailable).
    Returns whether today's date is in this list of bank holidays.
    """
    bank_holiday_json = None
    bank_holidays = [event["date"] for event in bank_holiday_json["england-and-wales"]["events"]]

    formatted_date = date.strftime("%Y-%m-%d")
    return formatted_date in bank_holidays


@background(schedule=datetime.combine(datetime.now(), SLA_UPDATE_TASK_TIME))
def update_cases_sla():
    date = datetime.now()
    if not is_bank_holiday(date) and not is_weekend(date):
        cases = Case.objects.filter(submitted_at__lt=datetime.combine(date, SLA_UPDATE_CUTOFF_TIME))
        return cases
