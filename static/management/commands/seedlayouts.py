from static.letter_layouts.models import LetterLayout
from static.management.SeedCommand import SeedCommandTest, SeedCommand

FILE = "lite_content/lite-api/document_layouts.csv"


class Command(SeedCommand):
    help = "Creates template layouts"
    success = "Successfully seeded layouts"
    seed_command = "seedlayouts"

    def operation(self, *args, **options):
        """
        pipenv run ./manage.py seedlayouts
        """
        csv = self.read_csv(FILE)
        self.update_or_create(LetterLayout, csv)
        self.delete_unused_objects(LetterLayout, csv)


class SeedLayoutsTests(SeedCommandTest):
    def test_seed_layouts(self):
        self.seed_command(Command)
        self.assertTrue(LetterLayout.objects.count() == len(Command.read_csv(FILE)))
