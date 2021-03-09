import argparse
from datetime import date
import csv
from tempfile import NamedTemporaryFile
from uuid import UUID

from openpyxl import Workbook

from django.core.management.base import BaseCommand
from django.db import connection

from api.reports.queries.ogl import OGL_SUMMARY
from api.reports.queries.standard import (
    GOODS_AND_RATINGS,
    LICENCES_WITH_GOOD_AMENDMENTS,
    SLA_CASES,
    APPLICATIONS_FINALISED_SUMMARY,
)

REPORT_QUERY_LOOKUP = {
    "ogl_summary": OGL_SUMMARY,
    "standard_applications_goods_and_ratings": GOODS_AND_RATINGS,
    "good_amendments": LICENCES_WITH_GOOD_AMENDMENTS,
    "sla_cases": SLA_CASES,
    "standard_applications_finalised_summary": APPLICATIONS_FINALISED_SUMMARY,
}


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "report_names",
            choices=REPORT_QUERY_LOOKUP.keys(),
            nargs="+",
            type=str,
            help="Name(s) of reports to generate",
        )
        parser.add_argument(
            "out_file", type=argparse.FileType("wb"), help="File to save .xslx output to, can be '-' to use stdout"
        )
        parser.add_argument("start_date", type=date, nargs="?", help="Start date for report", default=date.min)
        parser.add_argument("end_date", type=date, nargs="?", help="End date for report", default=date.max)

    def handle(self, *args, **options):
        out_file = options.pop("out_file")
        for report_name in options["report_names"]:
            query = REPORT_QUERY_LOOKUP[report_name]
            if isinstance(query, dict):
                with NamedTemporaryFile(suffix=".xlsx", delete=True) as temp_file:
                    wb = Workbook(write_only=True)
                    with connection.cursor() as cursor:
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
                    temp_file.seek(0)
                    if out_file.name == "<stdout>":
                        out_file.buffer.write(temp_file.read())
                    else:
                        out_file.write(temp_file.read())

            else:
                self.query_to_csv(options, query)

    def query_to_csv(self, options, query):
        with connection.cursor() as cursor:
            cursor.execute(query, options)
            desc = cursor.description
            headers = [x.name for x in desc]
            csvfile = csv.writer(self.stdout)
            csvfile.writerow(headers)
            rows = cursor.fetchall()
            csvfile.writerows(rows)


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
