from openpyxl import load_workbook

from static.control_list_entries.models import ControlListEntry
from static.control_list_entries.parser import parse_list_into_control_list_entries
from static.management.SeedCommand import SeedCommand, SeedCommandTest


class Command(SeedCommand):
    help = 'Creates and updates control list entries based off of the control list entry spreadsheet'
    success = 'Successfully seeded control list entries'
    seed_command = 'seedcontrollistentries'

    def operation(self, *args, **options):
        """
        pipenv run ./manage.py seedcontrollistentries
        """
        wb = load_workbook('lite_content/lite-permissions-finder/spreadsheet.xlsx', data_only=True)

        # Ignore first two sheets as they aren't relevant to control list entries
        wb.remove_sheet(wb.worksheets[0])
        wb.remove_sheet(wb.worksheets[0])

        # Loop through remaining sheets
        for sheet in wb.worksheets:
            parse_list_into_control_list_entries(sheet)


class SeedControlListEntriesTests(SeedCommandTest):
    def test_seed_control_list_entries(self):
        self.seed_command(Command)
        self.assertTrue(ControlListEntry.objects.count() > 3000)
