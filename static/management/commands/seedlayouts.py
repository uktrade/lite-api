import os

from django.db import transaction

from conf.settings import BASE_DIR
from static.letter_layouts.models import LetterLayout
from static.management.SeedCommand import SeedCommandTest, SeedCommand

LAYOUTS_FILE = "lite_content/lite_api/document_layouts.csv"


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedlayouts
    """

    help = "Creates template layouts"
    info = "Seeding layouts"
    success = "Successfully seeded layouts"
    seed_command = "seedlayouts"

    @transaction.atomic
    def operation(self, *args, **options):
        """
        pipenv run ./manage.py seedlayouts
        """
        csv = self.read_csv(LAYOUTS_FILE)
        self.update_or_create(LetterLayout, csv)
        self.delete_unused_objects(LetterLayout, csv)


class SeedLayoutsTests(SeedCommandTest):
    def test_seed_layouts(self):
        self.seed_command(Command)
        csv = Command.read_csv(LAYOUTS_FILE)
        html_layouts = os.listdir(os.path.join(BASE_DIR, "letter_templates", "layouts"))
        for row in csv:
            self.assertTrue(f"{row['filename']}.html" in html_layouts)
        self.assertTrue(LetterLayout.objects.count() == len(csv))
