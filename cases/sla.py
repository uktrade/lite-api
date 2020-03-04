import logging
from datetime import datetime, time

from background_task import background
from django.db import transaction
from django.db.models import F
from django.utils.timezone import now, make_aware

from cases.enums import CaseTypeSubTypeEnum
from cases.models import Case
from common.dates import is_weekend, is_bank_holiday

SLA_UPDATE_TASK_TIME = time(0, 0, 0)
SLA_UPDATE_CUTOFF_TIME = time(18, 0, 0)
LOG_PREFIX = "update_cases_sla background task:"

STANDARD_APPLICATION_TARGET_DAYS = 20
OPEN_APPLICATION_TARGET_DAYS = 60
MOD_CLEARANCE_TARGET_DAYS = 30


def get_application_target_sla(_type):
    if _type == CaseTypeSubTypeEnum.STANDARD:
        return STANDARD_APPLICATION_TARGET_DAYS
    elif _type == CaseTypeSubTypeEnum.OPEN:
        return OPEN_APPLICATION_TARGET_DAYS
    elif _type in [CaseTypeSubTypeEnum.EXHIBITION, CaseTypeSubTypeEnum.F680, CaseTypeSubTypeEnum.GIFTING]:
        return MOD_CLEARANCE_TARGET_DAYS


@background(schedule=make_aware(datetime.combine(now(), SLA_UPDATE_TASK_TIME)))
def update_cases_sla():
    """
    Updates all applicable cases SLA.
    Runs as a background task daily at a given time.
    Doesn't run on non-working days (bank-holidays & weekends)
    :return: How many cases the SLA was updated for or False if error / not ran
    """

    logging.info(f"{LOG_PREFIX} SLA Update Started")
    date = now()
    if not is_bank_holiday(date) and not is_weekend(date):
        try:
            # Get cases submitted before the cutoff time today, where they have never been closed
            # and where the cases SLA haven't been updated today (to avoid running twice in a single day).
            # Lock with select_for_update()
            # Increment the sla_days, decrement the sla_remaining_days & update sla_updated_at
            with transaction.atomic():
                results = (
                    Case.objects.select_for_update()
                    .filter(
                        submitted_at__lt=make_aware(datetime.combine(date, SLA_UPDATE_CUTOFF_TIME)),
                        last_closed_at__isnull=True,
                        sla_remaining_days__isnull=False,
                    )
                    .exclude(sla_updated_at__day=date.day)
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
