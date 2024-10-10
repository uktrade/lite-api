from django.db import transaction
from openpyxl import load_workbook
import csv
from api.staticdata.control_list_entries.parser import parse_list_into_control_list_entries
from api.staticdata.management.SeedCommand import SeedCommand


class Command(SeedCommand):
    """
    pipenv run ./manage.py extractcontrollistentries
    """

    help = "extract control list entries based off of the control list entry spreadsheet"
    info = "extract control list entries"
    seed_command = "extractcontrollistentries"

    @transaction.atomic
    def operation(self, *args, **options):
        wb = load_workbook("lite_content/lite-permissions-finder/spreadsheet.xlsx", data_only=True)

        # Ignore first two sheets as they aren't relevant to control list entries
        wb.remove_sheet(wb.worksheets[0])
        wb.remove_sheet(wb.worksheets[0])

        # Loop through remaining sheets
        cles = []
        for sheet in wb.worksheets:
            cles.extend(parse_list_into_control_list_entries(sheet))

        # write each line to csv
        with open("CLE.csv", "w", newline="") as csvfile:
            writer = csv.DictWriter(
                csvfile, fieldnames=["rating", "controlled", "parent", "text", "selectable_for_assessment", "category"]
            )
            writer.writeheader()
            writer.writerows(cles)
