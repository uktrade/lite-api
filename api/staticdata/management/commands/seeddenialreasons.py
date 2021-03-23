from django.db import transaction

from api.staticdata.denial_reasons.models import DenialReason
from api.staticdata.management.SeedCommand import SeedCommand

DENIAL_REASONS_FILE = "lite_content/lite_api/denial_reasons.csv"


class Command(SeedCommand):
    """
    pipenv run ./manage.py seeddenialreasons
    """

    help = "Seeds denial reasons"
    info = "Seeding denial reasons"
    seed_command = "seeddenialreasons"

    @transaction.atomic
    def operation(self, *args, **options):
        csv = self.read_csv(DENIAL_REASONS_FILE)
        filtered_csv = [{"id": row["id"], "deprecated": row["deprecated"]} for row in csv]
        self.update_or_create(DenialReason, filtered_csv)
        self.delete_unused_objects(DenialReason, filtered_csv)
