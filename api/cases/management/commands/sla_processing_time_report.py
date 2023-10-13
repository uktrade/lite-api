import logging
from datetime import datetime, time, timedelta

from background_task import background
from django.conf import settings
from django.db.models import F
from django.db.models import Q
from django.utils import timezone
from pytz import timezone as tz

from api.cases.models import EcjuQuery
from api.common.dates import is_weekend, is_bank_holiday
from api.audit_trail.models import Audit, AuditType


# DST safe version of midnight
SLA_UPDATE_TASK_TIME = time(22, 30, 0)
SLA_UPDATE_CUTOFF_TIME = time(18, 0, 0)
LOG_PREFIX = "update_cases_sla background task:"
import csv

def get_all_case_sla():
    case_sla_records = []
    for case in Case.objects.all():
        case_sla_records.append(get_case_sla(case.id))

    with open("case_sla.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["id", "case_ref", "elapsed_days", "working_days", "rfi_queries", "elapsed__rfi_days", "rfi_working_days", "sla_days"])
        for case_sla_record in case_sla_records:
            writer.writerow(case_sla_record.values())


def get_case_sla(case_id):

    date = timezone.localtime()
    case = Case.objects.get(id=case_id)
    elapsed_days = 0
    working_days = 0
    sla_days = 0
    rfi_working_days = 0
    rfi_non_working_days = 0

    start_date = get_start_date(case)
    end_date = get_end_date(case)

    for date in daterange(start_date, end_date):
        elapsed_days += 1
        if not is_bank_holiday(date, call_api=True) and not is_weekend(date):
            working_days += 1
            if not is_active_ecju_queries(date, case_id):
                sla_days += 1
            else:
                rfi_working_days += 1
        elif is_active_ecju_queries(date, case_id):
            rfi_non_working_days += 1
    return {
            "id": case.id,
            "reference_code": case.reference_code,
            "elapsed_days": elapsed_days,
            "working_days": working_days,
            "rfi_queries": EcjuQuery.objects.filter(case_id=case_id).count(),
            "elapsed__rfi_days": rfi_working_days + rfi_non_working_days,
            "rfi_working_days": rfi_working_days,
            "sla_days": sla_days,
        }

def get_start_date(case):
    update_audit_logs = Audit.objects.filter(target_object_id=case.id, verb=AuditType.UPDATED_STATUS).order_by("created_at")
    for update_audit_log in update_audit_logs:
        if update_audit_log.payload.get("status", {}).get("new") == "submitted":
            return update_audit_log.created_at
    return case.created_at

def get_end_date(case):
    update_audit_logs = Audit.objects.filter(target_object_id=case.id, verb=AuditType.UPDATED_STATUS).order_by("-created_at")
    for update_audit_log in update_audit_logs:
        if update_audit_log.payload.get("status", {}).get("new") == "finalised":
            return update_audit_log.created_at
    return case.updated_at


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days + 2)):
        yield start_date + timedelta(n)


def is_active_ecju_queries(date, case_id):
    compare_date_min = datetime.combine(date, time.min)
    compare_date_max = datetime.combine(date, time.max)

    return EcjuQuery.objects.filter(
        Q(responded_at__isnull=True, created_at__lte=compare_date_min)
        | Q(created_at__lte=compare_date_min) & Q(responded_at__gte=compare_date_max)
        | Q(created_at__range=(compare_date_min, compare_date_max)),
        Q(case_id=case_id),
    ).exists()
