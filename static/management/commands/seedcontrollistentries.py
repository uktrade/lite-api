from django.db import transaction
from openpyxl import load_workbook

from static.control_list_entries.parser import parse_list_into_control_list_entries
from static.management.SeedCommand import SeedCommand


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedcontrollistentries
    """

    help = "Creates and updates control list entries based off of the control list entry spreadsheet"
    info = "Seeding control list entries"
    seed_command = "seedcontrollistentries"

    @transaction.atomic
    def operation(self, *args, **options):
        wb = load_workbook("lite_content/lite-permissions-finder/spreadsheet.xlsx", data_only=True)

        # Ignore first two sheets as they aren't relevant to control list entries
        wb.remove_sheet(wb.worksheets[0])
        wb.remove_sheet(wb.worksheets[0])

        # Loop through remaining sheets
        for sheet in wb.worksheets:
            parse_list_into_control_list_entries(sheet)
