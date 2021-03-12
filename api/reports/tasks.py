import csv
import logging

from background_task import background
from datetime import date
from django.conf import settings
from django.db import connection
from openpyxl import Workbook
from tempfile import NamedTemporaryFile
from uuid import UUID

from api.reports.queries.ogl import OGL_SUMMARY
from api.reports.queries.standard import (
    GOODS_AND_RATINGS,
    LICENCES_WITH_GOOD_AMENDMENTS,
    SLA_CASES,
    APPLICATIONS_FINALISED_SUMMARY,
)
from gov_notify.client import LiteNotificationClient
from notifications_python_client import prepare_upload, errors

REPORT_QUERY_LOOKUP = {
    "ogl_summary": OGL_SUMMARY,
    "standard_applications_goods_and_ratings": GOODS_AND_RATINGS,
    "good_amendments": LICENCES_WITH_GOOD_AMENDMENTS,
    "sla_cases": SLA_CASES,
    "standard_applications_finalised_summary": APPLICATIONS_FINALISED_SUMMARY,
}

EMAIL_REPORTS_QUEUE = "email_reports_queue"

logger = logging.getLogger(__name__)
notify_client = LiteNotificationClient(settings.GOV_NOTIFY_KEY)

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

    with NamedTemporaryFile(prefix=report_name, suffix=suffix, mode=mode, delete=True) as temp_file:
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

        # send email using gov uk notify
        try:
            for recipient in settings.LITE_REPORTS_RECIPIENTS:
                temp_file.seek(0)
                with open(temp_file.name, "rb") as f:
                    data = {
                        "report_filename": temp_file.name.split("/")[-1],
                        "link_to_file": prepare_upload(f, is_csv=True),
                    }
                    response = notify_client.send_email(recipient, settings.LITE_REPORTS_EMAIL_TEMPLATE_ID, data)
                    logger.info(response)
        except errors.HTTPError as err:
            raise err


@background(queue=EMAIL_REPORTS_QUEUE, schedule=0)
def email_reports_task():
    """Task that generates the reports and emails them"""

    logger.info("Polling inbox for updates")

    try:
        for report_name, query in REPORT_QUERY_LOOKUP.items():
            email_report(report_name, query)

    except Exception as exc:  # noqa
        logging.error(f"An unexpected error occurred when emailing reports -> {type(exc).__name__}: {exc}")
        raise exc
