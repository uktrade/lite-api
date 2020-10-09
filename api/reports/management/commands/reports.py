from datetime import date
import csv

from django.core.management.base import BaseCommand
from django.db import connection

from api.reports.queries.ogl import OGL_SUMMARY
from api.reports.queries.standard import GOODS_AND_RATINGS

REPORT_QUERY_LOOKUP = {"ogl_summary": OGL_SUMMARY, "standard_applications_goods_and_ratings": GOODS_AND_RATINGS}


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "report_names",
            choices=REPORT_QUERY_LOOKUP.keys(),
            nargs="+",
            type=str,
            help="Name(s) of reports to generate",
        )
        parser.add_argument("start_date", type=date, nargs="?", help="Start date for report", default=date.min)
        parser.add_argument("end_date", type=date, nargs="?", help="End date for report", default=date.max)

    def handle(self, *args, **options):
        for report_name in options["report_names"]:
            query = REPORT_QUERY_LOOKUP[report_name]
            with connection.cursor() as cursor:
                cursor.execute(query, options)
                desc = cursor.description
                headers = [x.name for x in desc]
                csvfile = csv.writer(self.stdout)
                csvfile.writerow(headers)
                rows = cursor.fetchall()
                csvfile.writerows(rows)
