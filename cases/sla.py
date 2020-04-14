import logging
from datetime import datetime, time

from background_task import background
from django.db import transaction
from django.db.models import F
from django.db.models import Q
from django.utils import timezone

from cases.enums import CaseTypeSubTypeEnum
from cases.models import Case
from cases.models import EcjuQuery
from common.dates import is_weekend, is_bank_holiday

# DST safe version of midnight
SLA_UPDATE_TASK_TIME = time(22, 30, 0)
SLA_UPDATE_CUTOFF_TIME = time(18, 0, 0)
LOG_PREFIX = "update_cases_sla background task:"

STANDARD_APPLICATION_TARGET_DAYS = 20
OPEN_APPLICATION_TARGET_DAYS = 60
HMRC_QUERY_TARGET_DAYS = 2
MOD_CLEARANCE_TARGET_DAYS = 30


def get_application_target_sla(_type):
    if _type == CaseTypeSubTypeEnum.STANDARD:
        return STANDARD_APPLICATION_TARGET_DAYS
    elif _type == CaseTypeSubTypeEnum.OPEN:
        return OPEN_APPLICATION_TARGET_DAYS
    elif _type == CaseTypeSubTypeEnum.HMRC:
        return HMRC_QUERY_TARGET_DAYS
    elif _type in [CaseTypeSubTypeEnum.EXHIBITION, CaseTypeSubTypeEnum.F680, CaseTypeSubTypeEnum.GIFTING]:
        return MOD_CLEARANCE_TARGET_DAYS


def today(time=timezone.now().time()):
    """
    returns today's date with the provided time
    """
    return datetime.combine(timezone.now(), time, tzinfo=timezone.utc)


def yesterday(date=timezone.now(), time=None):
    """
    returns the previous working day from the date provided (defaults to now) at the time provided (defaults to now)
    """
    day = date - timezone.timedelta(days=1)

    while is_bank_holiday(day, call_api=False) or is_weekend(day):
        day = day - timezone.timedelta(days=1)
    if time:
        day = datetime.combine(day.date(), time, tzinfo=timezone.utc)
    return day


def get_case_ids_with_active_ecju_queries(date):
    # ECJU Query SLA exclusion criteria
    # 1. Still open & created before cutoff time today
    # 2. Responded to in the last working day before cutoff time today
    return (
        EcjuQuery.objects.filter(
            Q(responded_at__isnull=True, created_at__lt=today(time=SLA_UPDATE_CUTOFF_TIME),)
            | Q(responded_at__gt=yesterday(time=SLA_UPDATE_CUTOFF_TIME))
        )
        .values("case_id")
        .distinct()
    )


@background(schedule=datetime.combine(timezone.now(), SLA_UPDATE_TASK_TIME, tzinfo=timezone.utc))
def update_cases_sla():
    """
    Updates all applicable cases SLA.
    Runs as a background task daily at a given time.
    Doesn't run on non-working days (bank-holidays & weekends)
    :return: How many cases the SLA was updated for or False if error / not ran
    """

    logging.info(f"{LOG_PREFIX} SLA Update Started")
    date = timezone.now()
    if not is_bank_holiday(date, call_api=True) and not is_weekend(date):
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
                        submitted_at__lt=datetime.combine(date, SLA_UPDATE_CUTOFF_TIME, tzinfo=timezone.utc),
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
