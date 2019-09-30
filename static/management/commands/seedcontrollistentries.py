from django.core.management import BaseCommand
from django.db import transaction
from openpyxl import load_workbook

from static.control_list_entries.models import ControlListEntry
from static.control_list_entries.parser import parse_list_into_control_list_entries


class Command(BaseCommand):
    help = 'Creates and updates control list entries based off of the control list entry spreadsheet'

    @transaction.atomic
    def handle(self, *args, **options):
        """
        pipenv run ./manage.py seedcontrollistentries
        """
        wb = load_workbook('lite-content/lite-permissions-finder/spreadsheet.xlsx', data_only=True)

        # Ignore first two sheets as they aren't relevant to control list entries
        wb.remove_sheet(wb.worksheets[0])
        wb.remove_sheet(wb.worksheets[0])

        # Clear the control list entry database
        ControlListEntry.objects.all().delete()

        # Loop through remaining sheets
        for sheet in wb.worksheets:
            parse_list_into_control_list_entries(sheet)

        self.stdout.write(self.style.SUCCESS('Control List Entries updated successfully!'))
