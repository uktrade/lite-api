import csv
import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from api.applications.models import StandardApplication


class Command(BaseCommand):
    help = """
        Command to add/update Annual report summary (ARS) value for a given goods line item.

        ARS is a mandatory field and will not be empty if a product is reviewed but because of
        a previous bug it was possible that this can be empty even after it is reviewed. The
        bug is fixed now but some products still have this as empty which affects reporting data
        hence this command is created to manually fix them.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "report_summary_file",
            type=str,
            help="CSV file containing ARS data to be updated",
        )

    def handle(self, *args, **options):
        report_summary_file = options.pop("report_summary_file")

        with transaction.atomic():
            report_summary_data = csv.DictReader(open(report_summary_file))

            for row in report_summary_data:
                case_reference = row["case_reference"]
                line_item = int(row["line_item"])
                updated_report_summary = row["updated_report_summary"]

                try:
                    application = StandardApplication.objects.get(reference_code=case_reference)
                except StandardApplication.DoesNotExist:
                    logging.error("Case (%s) not found, please provide valid case reference", case_reference)
                    return

                num_products = len(application.goods.all())
                if line_item <= 0 or line_item > num_products:
                    logging.error("Invalid line item, %s has only %d products", case_reference, num_products)
                    return

                good_on_application = application.goods.all()[line_item - 1]

                good_on_application.report_summary = updated_report_summary
                good_on_application.save()

                logging.info(
                    "[%s] Updated report summary for line item %d (product name: %s) is: %s",
                    case_reference,
                    line_item,
                    good_on_application.good.name,
                    good_on_application.report_summary,
                )
