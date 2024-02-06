from datetime import datetime, time

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.db.models import Q
from django.utils import timezone
from pytz import timezone as tz

from api.cases.enums import CaseTypeSubTypeEnum
from api.cases.models import Case, CaseAssignmentSLA, CaseQueue, DepartmentSLA, EcjuQuery
from api.common.dates import is_weekend, is_bank_holiday
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus
from api.cases.notify import notify_exporter_ecju_query_chaser


# DST safe version of midnight
SLA_UPDATE_CUTOFF_TIME = time(18, 0, 0)

STANDARD_APPLICATION_TARGET_DAYS = 20
OPEN_APPLICATION_TARGET_DAYS = 60
HMRC_QUERY_TARGET_DAYS = 2
MOD_CLEARANCE_TARGET_DAYS = 30


logger = get_task_logger(__name__)


def get_application_target_sla(_type):
    if _type == CaseTypeSubTypeEnum.STANDARD:
        return STANDARD_APPLICATION_TARGET_DAYS
    elif _type == CaseTypeSubTypeEnum.OPEN:
        return OPEN_APPLICATION_TARGET_DAYS
    elif _type == CaseTypeSubTypeEnum.HMRC:
        return HMRC_QUERY_TARGET_DAYS
    elif _type in [CaseTypeSubTypeEnum.EXHIBITION, CaseTypeSubTypeEnum.F680, CaseTypeSubTypeEnum.GIFTING]:
        return MOD_CLEARANCE_TARGET_DAYS


def today(time=None):
    """
    returns today's date with the provided time
    """
    if not time:
        time = timezone.localtime().time()

    return datetime.combine(timezone.localtime(), time, tzinfo=tz(settings.TIME_ZONE))


def yesterday(date=None, time=None):
    """
    returns the previous working day from the date provided (defaults to now) at the time provided (defaults to now)
    """
    if not date:
        date = timezone.localtime()

    day = date - timezone.timedelta(days=1)

    while is_bank_holiday(day, call_api=False) or is_weekend(day):
        day = day - timezone.timedelta(days=1)

    if time:
        day = datetime.combine(day.date(), time, tzinfo=tz(settings.TIME_ZONE))

    return day


def get_case_ids_with_active_ecju_queries(date):
    # ECJU Query SLA exclusion criteria
    # 1. Still open & created before cutoff time today
    # 2. Responded to in the last working day before cutoff time today
    return (
        EcjuQuery.objects.filter(
            Q(responded_at__isnull=True, created_at__lt=today(time=SLA_UPDATE_CUTOFF_TIME))
            | Q(responded_at__gt=yesterday(time=SLA_UPDATE_CUTOFF_TIME))
        )
        .values("case_id")
        .distinct()
    )


MAX_ATTEMPTS = 3
RETRY_BACKOFF = 180


@shared_task(
    autoretry_for=(Exception,),
    max_retries=MAX_ATTEMPTS,
    retry_backoff=RETRY_BACKOFF,
)
def update_cases_sla():
    """
    Updates all applicable cases SLA.
    Runs as a background task daily at a given time.
    Doesn't run on non-working days (bank-holidays & weekends)
    :return: How many cases the SLA was updated for or False if error / not ran
    """

    logger.info("SLA Update Started")
    date = timezone.localtime()
    if not is_bank_holiday(date, call_api=True) and not is_weekend(date):
        try:

            # Get cases submitted before the cutoff time today, where they have never been closed
            # and where the cases SLA haven't been updated today (to avoid running twice in a single day).
            # Lock with select_for_update()
            # Increment the sla_days, decrement the sla_remaining_days & update sla_updated_at
            active_ecju_query_cases = get_case_ids_with_active_ecju_queries(date)
            terminal_case_status = CaseStatus.objects.filter(status__in=CaseStatusEnum.terminal_statuses())
            cases = (
                Case.objects.filter(
                    submitted_at__lt=datetime.combine(date, SLA_UPDATE_CUTOFF_TIME, tzinfo=tz(settings.TIME_ZONE)),
                    last_closed_at__isnull=True,
                    sla_remaining_days__isnull=False,
                )
                .exclude(Q(sla_updated_at__day=date.day) | Q(id__in=active_ecju_query_cases))
                .exclude(status__in=terminal_case_status)
            )
            with transaction.atomic():
                # Keep track of the department SLA updates.
                # We only want to update a department SLA once per case assignment per day.
                department_slas_updated = set()
                for assignment in CaseQueue.objects.filter(case__in=cases):
                    # Update team SLAs
                    try:
                        assignment_sla = CaseAssignmentSLA.objects.get(queue=assignment.queue, case=assignment.case)
                        assignment_sla.sla_days += 1
                        assignment_sla.save()
                    except CaseAssignmentSLA.DoesNotExist:
                        CaseAssignmentSLA.objects.create(queue=assignment.queue, case=assignment.case, sla_days=1)
                    # Update department SLAs
                    department = assignment.queue.team.department
                    if department is not None:
                        try:
                            department_sla = DepartmentSLA.objects.get(department=department, case=assignment.case)
                            if department_sla.id not in department_slas_updated:
                                department_sla.sla_days += 1
                                department_sla.save()
                        except DepartmentSLA.DoesNotExist:
                            department_sla = DepartmentSLA.objects.create(
                                department=department, case=assignment.case, sla_days=1
                            )
                        department_slas_updated.add(department_sla.id)

                results = cases.select_for_update().update(
                    sla_days=F("sla_days") + 1, sla_remaining_days=F("sla_remaining_days") - 1, sla_updated_at=date
                )

            logger.info(f"SLA Update Successful. Updated {results} cases")
            return results
        except Exception as e:  # noqa
            logger.error(e)
            return False

    logger.info("SLA Update Not Performed. Non-working day")
    return False


WORKING_DAYS_ECJU_QUERY_CHASER_REMINDER = 15
WORKING_DAYS_APPLICATION = 20


@shared_task(
    autoretry_for=(Exception,),
    max_retries=MAX_ATTEMPTS,
    retry_backoff=RETRY_BACKOFF,
)
def schedule_all_ecju_query_chaser_emails():
    """
    Sends an ECJU 15 working days reminder
    Runs as a background task daily at a given time.
    Doesn't run on non-working days (bank-holidays & weekends)
    """
    logger.info("Sending all ECJU query chaser emails started")

    try:
        ecju_query_reminders = []
        ecju_queries = EcjuQuery.objects.filter(
            Q(is_query_closed=False) & Q(chaser_email_sent_on__isnull=True) & Q(case__status__is_terminal=False)
        )

        for ecju_query in ecju_queries:
            if (
                ecju_query.open_working_days >= WORKING_DAYS_ECJU_QUERY_CHASER_REMINDER
                and ecju_query.open_working_days <= WORKING_DAYS_APPLICATION
            ):
                ecju_query_reminders.append(ecju_query.id)

        for ecju_query_id in ecju_query_reminders:
            # Now lets loop round and send the notifications
            send_ecju_query_chaser_email.delay(ecju_query_id)

        logger.info("Sending all ECJU query chaser emails started finished")

    except Exception as e:  # noqa
        logger.error(e)
        raise e


@shared_task(
    autoretry_for=(Exception,),
    max_retries=MAX_ATTEMPTS,
    retry_backoff=RETRY_BACKOFF,
)
def send_ecju_query_chaser_email(ecju_query_id):
    """
    Sends an ecju query chaser email based on a case
    Call back is to mark the relevent queries as chaser sent
    """
    logger.info("Sending ECJU Query chaser emails for ecju_query_id %s started", ecju_query_id)
    try:
        notify_exporter_ecju_query_chaser(ecju_query_id, callback=mark_ecju_queries_as_sent.si(ecju_query_id))
        logger.info("Sending ECJU Query chaser email for ecju_query_id %s finished", ecju_query_id)
    except Exception as e:  # noqa
        logger.error(e)
        raise e


@shared_task
def mark_ecju_queries_as_sent(ecju_query_id):
    """
    Used as a call back method to set chaser_email_sent once a chaser email has been sent
    """
    logger.info("Mark ECJU queries with chaser_email_sent as true for ecju_query_ids (%s) ", ecju_query_id)
    ecju_query = EcjuQuery.objects.get(chaser_email_sent_on__isnull=True, id=ecju_query_id)
    ecju_query.chaser_email_sent_on = timezone.datetime.now()
    # Save base so we don't impact any over fields
    ecju_query.save_base()
