import csv
import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from api.teams.models import Team

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """Update team records from a CSV file.

    The first line in the file is a header that consists of the field names on the Team model
    to update. A subset of field names can be specified, but the first column must always be `id`.

    For example, to update just the team name and is_ogd attribute for two teams, the file would contain:

        id,name,is_ogd
        57c341d6-7a28-473f-a6c8-5952742b6b03,team1_new_name,true
        94996aa5-f494-4116-9e74-d757d39c5ee8,team2_new_name,false
    """

    help = "Updates teams from a CSV input file"

    def add_arguments(self, parser):
        parser.add_argument("input_csv", type=str, help="Path to the input CSV file")
        parser.add_argument(
            "--dry", action="store_true", help="Print out what action will happen without applying any changes"
        )

    def handle(self, *args, **options):
        dry_run = options["dry"]
        if dry_run:
            log.info("Dry run only, no changes will be applied")

        with open(options["input_csv"]) as w:
            reader = csv.DictReader(w)
            to_update = [{k: v.strip() for k, v in record.items()} for record in reader]

        with transaction.atomic():
            for record in to_update:
                team = Team.objects.filter(id=record.pop("id"))  # id must always exist
                log.info(f"Updating '{team[0].name}' with {record}")

                if not dry_run:
                    converters = {
                        "name": str,
                        "department": lambda x: str(x) if x else None,
                        "part_of_ecju": lambda x: x.lower() == "true",
                        "is_ogd": lambda x: x.lower() == "true",
                    }

                    team.update(
                        **{attr_name: converters[attr_name](attr_val) for attr_name, attr_val in record.items()}
                    )
