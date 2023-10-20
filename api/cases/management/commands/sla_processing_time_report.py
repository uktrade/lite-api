from datetime import datetime, time, timedelta
from django.db.models import Q
from django.conf import settings
from django.utils import timezone
from pytz import timezone as tz

from api.cases.models import EcjuQuery
from api.common.dates import is_weekend, is_bank_holiday
from api.audit_trail.models import Audit, AuditType
from api.cases.models import Case

SLA_CUTOFF_START_TIME = time(9, 0, 0)
SLA_CUTOFF_END_TIME = time(17, 0, 0)


def get_all_case_sla():
    case_sla_records = []
    for case in Case.objects.all():
        case_sla_records.append(get_case_sla(case))
    return case_sla_records


def today(time=None):
    """
    returns today's date with the provided time
    """
    if not time:
        time = timezone.localtime().time()
    return datetime.combine(timezone.localtime(), time, tzinfo=tz(settings.TIME_ZONE))


def get_case_sla(case):

    elapsed_days = 0
    working_days = 0
    sla_days = 0
    rfi_working_days = 0
    rfi_non_working_days = 0

    start_date = get_start_date(case)
    end_date = get_end_date(case)

    if start_date:
        for date in daterange(start_date, end_date):
            elapsed_days += 1
            if not is_bank_holiday(date, call_api=False) and not is_weekend(date):
                # `Check cut off time for on `start_date
                working_days += 1
                if not is_active_ecju_queries(date, case.id):
                    sla_days += 1
                else:
                    rfi_working_days += 1
            elif is_active_ecju_queries(date, case.id):
                rfi_non_working_days += 1

    return {
        "id": case.id,
        "reference_code": case.reference_code,
        "elapsed_days": elapsed_days,
        "working_days": working_days,
        "rfi_queries": EcjuQuery.objects.filter(case_id=case.id).count(),
        "elapsed__rfi_days": rfi_working_days + rfi_non_working_days,
        "rfi_working_days": rfi_working_days,
        "sla_days": sla_days,
        "start_date": start_date,
        "end_date": end_date,
    }


def get_start_date(case):
    update_audit_logs = Audit.objects.filter(target_object_id=case.id, verb=AuditType.UPDATED_STATUS).order_by(
        "created_at"
    )
    for update_audit_log in update_audit_logs:
        if update_audit_log.payload.get("status", {}).get("new", "").lower() == "submitted":
            return update_audit_log.created_at


def get_end_date(case):
    update_audit_logs = Audit.objects.filter(target_object_id=case.id, verb=AuditType.UPDATED_STATUS).order_by(
        "-created_at"
    )
    for update_audit_log in update_audit_logs:
        if update_audit_log.payload.get("status", {}).get("new", "").lower() in ("finalised", "withdrawn"):
            return update_audit_log.created_at
    return today(time=SLA_CUTOFF_END_TIME)


def is_inside_sla_time(startdate, enddate):
    return startdate < today(SLA_CUTOFF_END_TIME) and enddate.time() > today(SLA_CUTOFF_START_TIME)


def daterange(start_date, end_date):
    days_dif = int((datetime.combine(end_date, time.max) - datetime.combine(start_date, time.max)).days) + 1
    for n in range(days_dif):
        days_dif -= 1
        if days_dif == 0:
            yield end_date
        else:
            yield start_date + timedelta(n)


def is_active_ecju_queries(date, case_id):
    date_start_time = datetime.combine(date, time.min)
    date_end_time = datetime.combine(date, time.max)
    return EcjuQuery.objects.filter(
        Q(responded_at__isnull=True, created_at__lte=date_end_time)
        | Q(created_at__lte=date_end_time) & Q(responded_at__gte=date_end_time)
        | Q(created_at__range=(date_start_time, date_end_time))
        | Q(responded_at__range=(date_start_time, date_end_time)),
        Q(case_id=case_id),
    ).exists()
