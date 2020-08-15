from django.db import transaction

from api.staticdata.letter_layouts.models import LetterLayout
from api.staticdata.management.SeedCommand import SeedCommand

LAYOUTS_FILE = "lite_content/lite_api/document_layouts.csv"


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedlayouts
    """

    help = "Creates template layouts"
    info = "Seeding template layouts"
    seed_command = "seedlayouts"

    @transaction.atomic
    def operation(self, *args, **options):
        csv = self.read_csv(LAYOUTS_FILE)
        self.update_or_create(LetterLayout, csv)
        self.delete_unused_objects(LetterLayout, csv)
