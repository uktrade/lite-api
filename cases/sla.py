import logging
from datetime import datetime, time
import requests

from background_task import background
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone
from rest_framework import status

from cases.enums import CaseTypeSubTypeEnum
from cases.models import Case, EcjuQuery

# DST safe version of midnight
SLA_UPDATE_TASK_TIME = time(22, 30, 0)
SLA_UPDATE_CUTOFF_TIME = time(18, 0, 0)
BANK_HOLIDAY_API = "https://www.gov.uk/bank-holidays.json"
BACKUP_FILE_NAME = "bank-holidays.csv"
LOG_PREFIX = "update_cases_sla background task:"

STANDARD_APPLICATION_TARGET_DAYS = 20
OPEN_APPLICATION_TARGET_DAYS = 60
MOD_CLEARANCE_TARGET_DAYS = 30


def get_application_target_sla(type):
    if type == CaseTypeSubTypeEnum.STANDARD:
        return STANDARD_APPLICATION_TARGET_DAYS
    elif type == CaseTypeSubTypeEnum.OPEN:
        return OPEN_APPLICATION_TARGET_DAYS
    elif type in [CaseTypeSubTypeEnum.EXHIBITION, CaseTypeSubTypeEnum.F680, CaseTypeSubTypeEnum.GIFTING]:
        return MOD_CLEARANCE_TARGET_DAYS


def is_weekend(date):
    # Weekdays are 0 indexed so Saturday is 5 and Sunday is 6
    return date.weekday() > 4


def get_bank_holidays(call_api=True):
    """
    Uses the GOV bank holidays API.
    If it can connect to the API, it extracts the list of bank holidays,
    saves a backup of this list as a CSV and returns the list.
    If it cannot connect to the service it will use the CSV backup and returns the list.
    """
    data = []
    if call_api:
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
    else:
        try:
            with open(BACKUP_FILE_NAME, "r") as backup_file:
                data = backup_file.read().split(",")
        except FileNotFoundError:
            logging.error(f"{LOG_PREFIX} No local bank holiday backup found; {BACKUP_FILE_NAME}")
    return data


def is_bank_holiday(date):
    formatted_date = date.strftime("%Y-%m-%d")
    return formatted_date in get_bank_holidays()


def yesterday(date=None):
    if date:
        day = date - timezone.timedelta(days=1)
    else:
        day = timezone.now() - timezone.timedelta(days=1)
    while is_bank_holiday(day) or is_weekend(day):
        day = day - timezone.timedelta(days=1)
    return day


def get_case_ids_with_active_ecju_queries(date):
    # ECJU Query SLA exclusion criteria
    # 1. Still open & created before cutoff time today
    # 2. Responded to in the last working day before cutoff time today
    return (
        EcjuQuery.objects.filter(
            Q(
                responded_at__isnull=True,
                created_at__lt=timezone.make_aware(datetime.combine(date, SLA_UPDATE_CUTOFF_TIME)),
            )
            | Q(
                responded_at__range=[
                    timezone.make_aware(datetime.combine(yesterday(), SLA_UPDATE_CUTOFF_TIME)),
                    timezone.make_aware(datetime.combine(date, SLA_UPDATE_CUTOFF_TIME)),
                ],
            )
        )
        .values("case")
        .distinct()
    )


@background(schedule=timezone.make_aware(datetime.combine(timezone.now(), SLA_UPDATE_TASK_TIME)))
def update_cases_sla():
    """
    Updates all applicable cases SLA.
    Runs as a background task daily at a given time.
    Doesn't run on non-working days (bank-holidays & weekends)
    :return: How many cases the SLA was updated for or False if error / not ran
    """

    logging.info(f"{LOG_PREFIX} SLA Update Started")
    date = timezone.now()
    if not is_bank_holiday(date) and not is_weekend(date):
        try:
            # Get cases submitted before the cutoff time today, where they have never been closed
            # and where the cases SLA haven't been updated today (to avoid running twice in a single day).
            # Lock with select_for_update()
            # Increment the sla_days, decrement the sla_remaining_days & update sla_updated_at
            with transaction.atomic():
                active_ecju_query_cases = get_case_ids_with_active_ecju_queries(date)
                results = (
                    Case.objects.select_for_update()
                    .filter(
                        submitted_at__lt=timezone.make_aware(datetime.combine(date, SLA_UPDATE_CUTOFF_TIME)),
                        last_closed_at__isnull=True,
                        sla_remaining_days__isnull=False,
                    )
                    .exclude(Q(sla_updated_at__day=date.day) | Q(id__in=active_ecju_query_cases))
                    .update(
                        sla_days=F("sla_days") + 1, sla_remaining_days=F("sla_remaining_days") - 1, sla_updated_at=date
                    )
                )
                logging.info(f"{LOG_PREFIX} SLA Update Successful. Updated {results} cases")
                return results
        except Exception as e:  # noqa
            logging.error(e)
            return False

    logging.info(f"{LOG_PREFIX} SLA Update Not Performed. Non-working day")
    return False
