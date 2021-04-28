import csv
import logging

from background_task import background
from datetime import date, datetime, time
from django.conf import settings
from django.core import mail
from django.db import connection
from django.utils import timezone
from openpyxl import Workbook
from pytz import timezone as tz
from tempfile import NamedTemporaryFile
from uuid import UUID

from api.reports.helpers import get_team_query_options
from api.reports.queries.standard import (
    GOODS_AND_RATINGS,
    LICENCES_WITH_GOOD_AMENDMENTS,
    SLA_CASES,
    APPLICATIONS_FINALISED_SUMMARY,
    MI_COMBINED_ALL_LIVE,
    STRATEGIC_EXPORT_CONTROLS_YEAR_QTR,
    MI_ELA_STATISTICS,
)

REPORT_QUERY_LOOKUP = {
    "standard_applications_goods_and_ratings": GOODS_AND_RATINGS,
    "good_amendments": LICENCES_WITH_GOOD_AMENDMENTS,
    "sla_cases": SLA_CASES,
    "standard_applications_finalised_summary": APPLICATIONS_FINALISED_SUMMARY,
    "mi_combined_all_live": MI_COMBINED_ALL_LIVE,
    "strategic_export_controls_year_qtr": STRATEGIC_EXPORT_CONTROLS_YEAR_QTR,
    "mi_ela_statistics": MI_ELA_STATISTICS,
}

EMAIL_REPORTS_TASK_TIME = time(6, 30, 0)
EMAIL_REPORTS_QUEUE = "email_reports_queue"

logger = logging.getLogger(__name__)

identity = lambda x: x


def serialize_cell(cell):
    serializers = {
        UUID: str,
    }
    converter = serializers.get(type(cell), identity)
    return converter(cell)


def serialize_row(row):
    # return row
    return [serialize_cell(cell) for cell in row]


def email_report(report_name, query):
    options = {
        "start_date": date.min,
        "end_date": date.max,
    }
    if isinstance(query, dict):
        suffix = ".xlsx"
        mode = "w+b"
    else:
        suffix = ".csv"
        mode = "w"

    if report_name == "mi_ela_statistics":
        team_options = get_team_query_options()
        query = query.format(**team_options)

    with NamedTemporaryFile(prefix=report_name + "_", suffix=suffix, mode=mode, delete=True) as temp_file:
        with connection.cursor() as cursor:
            if isinstance(query, dict):
                wb = Workbook(write_only=True)
                for tab_name, sql_query in query.items():
                    cursor.execute(sql_query, options)
                    desc = cursor.description
                    headers = [x.name for x in desc]
                    worksheet = wb.create_sheet(tab_name)
                    worksheet.append(headers)
                    rows = cursor.fetchall()
                    for row in rows:
                        worksheet.append(serialize_row(row))
                wb.save(temp_file.name)
            else:
                cursor.execute(query, options)
                desc = cursor.description
                headers = [x.name for x in desc]
                csvfile = csv.writer(temp_file)
                csvfile.writerow(headers)
                rows = cursor.fetchall()
                csvfile.writerows(rows)

            temp_file.flush()

        with mail.get_connection() as smtp_connection:
            temp_file.seek(0)
            report_filename = temp_file.name.split("/")[-1]
            subject = f"[LITE-Reports][{settings.ENV}][{date.today().strftime('%d-%m-%Y')}]"
            body = f"Please find attached the report {report_filename} with this email\n\n- LITE OPS Team"
            email = mail.EmailMessage(
                subject=f"{subject}: {report_filename}",
                body=body,
                from_email=settings.LITE_OPS_EMAIL,
                to=settings.LITE_REPORTS_RECIPIENTS,
                bcc=[],
                connection=smtp_connection,
            )

            email.attach_file(temp_file.name)
            email.send()


@background(schedule=datetime.combine(timezone.localtime(), EMAIL_REPORTS_TASK_TIME, tzinfo=tz(settings.TIME_ZONE)))
def email_reports_task():
    """Task that generates the reports and emails them"""

    if not settings.FEATURE_EMAIL_REPORTS_ENABLED:
        logger.info("Feature flag FEATURE_EMAIL_REPORTS_ENABLED to enable emailing reports not enabled")
        return

    try:
        for report_name, query in REPORT_QUERY_LOOKUP.items():
            logger.info(f"Generating and emailing report {report_name}")
            email_report(report_name, query)

    except Exception as exc:  # noqa
        logging.error(f"An unexpected error occurred when emailing reports -> {type(exc).__name__}: {exc}")
        raise exc
