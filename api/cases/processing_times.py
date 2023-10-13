import logging
from datetime import datetime, time, timedelta

from background_task import background
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.db.models import Q
from django.utils import timezone
from pytz import timezone as tz

from api.cases.enums import CaseTypeSubTypeEnum
from api.cases.models import Case, CaseAssignmentSLA, CaseQueue, DepartmentSLA
from api.cases.models import EcjuQuery
from api.common.dates import is_weekend, is_bank_holiday
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus

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


def setTime(date, time):
    """
    returns a date date with the provided time
    """
    if not date:
        date = timezone.localtime()

    if not time:
        time = timezone.localtime().time()

    return datetime.combine(date.date(), time, tzinfo=tz(settings.TIME_ZONE))


def increment_slas(case):
    assignment_sla = {}
    department_sla = {}
    department_slas_updated = set()
    for assignment in CaseQueue.objects.filter(case=case):
        # Update team SLAs
        try:
            queue_name = assignment.queue.name
            assigned = CaseAssignmentSLA.objects.get(queue=assignment.queue, case=assignment.case)
            if assigned:
                if assignment_sla.get(queue_name):
                    assignment_sla[queue_name] += 1
                else:
                    assignment_sla[queue_name] = 0
        except CaseAssignmentSLA.DoesNotExist:
            CaseAssignmentSLA.objects.create(queue=assignment.queue, case=assignment.case, sla_days=1)
        # Update department SLAs
        department = assignment.queue.team.department
        if department is not None:
            try:
                department_sla = DepartmentSLA.objects.get(department=department, case=assignment.case)
                if department_sla.id not in department_slas_updated:
                    if department_sla[department.name]:
                        department_sla[department.name] += 1
                    else:
                        department_sla[department.name] = 0
            except DepartmentSLA.DoesNotExist:
                department_sla = DepartmentSLA.objects.create(department=department, case=assignment.case, sla_days=1)
            department_slas_updated.add(department_sla.id)


def active_ecju_queries(id, date):
    # ECJU Query SLA exclusion criteria
    # 1. Still open & created before cutoff time today
    # 2. Responded to in the last working day before cutoff time today
    return EcjuQuery.objects.filter(
        Q(case_id=id)
        & Q(
            created_at__lt=setTime(date=date, time=SLA_UPDATE_CUTOFF_TIME),
            updated_at__gt=setTime(date=date, time=SLA_UPDATE_CUTOFF_TIME),
        )
    )


def ecju_queries_count(id):
    return len(EcjuQuery.objects.filter(Q(case_id=id)))


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days + 2)):
        yield start_date + timedelta(n)


def get_processing_times(reference_code):
    case = Case.objects.get(reference_code=reference_code)
    start = case.created_at
    end = case.updated_at

    sla_days = 0
    rfi_count = ecju_queries_count(case.id)
    rfi_days = 0
    rfi_working_days = 0
    total_days = 0
    working_days = 0

    for date in daterange(start, end):
        total_days += 1
        active_query = active_ecju_queries(case.id, date)
        if active_query:
            rfi_days += 1
            print(date)
        if not is_bank_holiday(date, call_api=True) and not is_weekend(date):
            working_days += 1
            active_query = active_ecju_queries(case.id, date)
            if active_query:
                rfi_working_days += 1
            if not active_query:
                sla_days += 1

    case_info = {
        "sla_days": sla_days,
        "rfi_count": rfi_count,
        "rfi_days": rfi_days,
        "rfi_working_days": rfi_working_days,
        "total_days": total_days,
        "working_days": working_days,
    }
    return case_info
