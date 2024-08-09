import uuid

from django.db import transaction

from api.staticdata.denial_reasons.models import DenialReason
from api.staticdata.management.SeedCommand import SeedCommand
from api.staticdata.denial_reasons.constants import DENIAL_REASON_ID_TO_UUID_MAP

DENIAL_REASONS_FILE = "lite_content/lite_api/denial_reasons_update.csv"


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
        filtered_csv = [
            {
                "id": row["id"],
                "uuid": uuid.UUID(DENIAL_REASON_ID_TO_UUID_MAP[row["id"]]),
                "display_value": row["display_value"],
                "deprecated": row["deprecated"],
                "description": row["description"],
            }
            for row in csv
        ]
        self.update_or_create(DenialReason, filtered_csv)
