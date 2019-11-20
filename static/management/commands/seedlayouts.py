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
        # Add layouts
        reader = self.read_csv(FILE)
        for row in reader:
            LetterLayout.objects.get_or_create(filename=row[1], name=row[2])
            print("Seeded %s layout" % row[2])


class SeedLayoutsTests(SeedCommandTest):
    def test_seed_layouts(self):
        self.seed_command(Command)
        self.assertTrue(LetterLayout.objects.count() == len(Command.read_csv(FILE)))
