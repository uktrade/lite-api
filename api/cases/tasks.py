import logging
from datetime import datetime, time

from background_task import background
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.db.models import Q
from django.utils import timezone
from pytz import timezone as tz

from gov_notify import service as gov_notify_service
from gov_notify.enums import TemplateType
from gov_notify.payloads import EcjuComplianceCreatedEmailData

from api.cases.models import (
    EcjuQuery,
    Case,
    CaseQueue,
    CaseAssignmentSLA,
    DepartmentSLA
)
from api.compliance.models import ComplianceVisitCase
from api.organisations.models import Site

from api.common.dates import is_weekend, is_bank_holiday

from api.cases.enums import (
    CaseTypeSubTypeEnum,
    CaseTypeTypeEnum,
    CaseTypeReferenceEnum,
)
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus

# DST safe version of midnight
SLA_UPDATE_TASK_TIME = time(22, 30, 0)
SLA_UPDATE_CUTOFF_TIME = time(18, 0, 0)
LOG_PREFIX = "update_cases_sla background task:"
EMAIL_NOTIFICATION_QUEUE = "email_notification_queue"

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


def yesterday(date=timezone.localtime(), time=None):
    """
    returns the previous working day from the date provided (defaults to now) at the time provided (defaults to now)
    """
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


@background(schedule=datetime.combine(timezone.localtime(), SLA_UPDATE_TASK_TIME, tzinfo=tz(settings.TIME_ZONE)))
def update_cases_sla():
    """
    Updates all applicable cases SLA.
    Runs as a background task daily at a given time.
    Doesn't run on non-working days (bank-holidays & weekends)
    :return: How many cases the SLA was updated for or False if error / not ran
    """

    logging.info(f"{LOG_PREFIX} SLA Update Started")
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

            logging.info(f"{LOG_PREFIX} SLA Update Successful. Updated {results} cases")
            return results
        except Exception as e:  # noqa
            logging.error(e)
            return False

    logging.info(f"{LOG_PREFIX} SLA Update Not Performed. Non-working day")
    return False


@background(queue=EMAIL_NOTIFICATION_QUEUE, schedule=0)
def send_ecju_query_emails(pk, serializer):

    # Send an email to the user(s) that submitted the application
    case_info = (
        Case.objects.annotate(email=F("submitted_by__baseuser_ptr__email"), name=F("baseapplication__name"))
        .values("id", "email", "name", "reference_code", "case_type__type", "case_type__reference")
        .get(id=pk)
    )

    # For each licence in a compliance case, email the user that submitted the application
    if case_info["case_type__type"] == CaseTypeTypeEnum.COMPLIANCE:
        emails = set()
        case_id = case_info["id"]
        link = f"{settings.EXPORTER_BASE_URL}/compliance/{pk}/ecju-queries/"

        if case_info["case_type__reference"] == CaseTypeReferenceEnum.COMP_VISIT:
            # If the case is a compliance visit case, use the parent compliance site case ID instead
            case_id = ComplianceVisitCase.objects.get(pk=case_id).site_case_id
            link = f"{settings.EXPORTER_BASE_URL}/compliance/{case_id}/visit/{pk}/ecju-queries/"

        site = Site.objects.get(compliance__id=case_id)

        for licence in Case.objects.filter_for_cases_related_to_compliance_case(case_id):
            emails.add(licence.submitted_by.email)

        for email in emails:
            gov_notify_service.send_email(
                email_address=email,
                template_type=TemplateType.ECJU_COMPLIANCE_CREATED,
                data=EcjuComplianceCreatedEmailData(
                    query=serializer.data["question"],
                    case_reference=case_info["reference_code"],
                    site_name=site.name,
                    site_address=str(site.address),
                    link=link,
                ),
            )
