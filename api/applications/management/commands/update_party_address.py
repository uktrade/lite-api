import csv

from django.core.management.base import BaseCommand

from api.parties.models import Party
from api.support.helpers import developer_intervention


class Command(BaseCommand):
    help = "Update address for multiple parties from a CSV file"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=open, help="The path to the CSV file containing updates")

    def handle(self, *args, **kwargs):
        csv_file = kwargs["csv_file"]

        reader = csv.DictReader(csv_file)
        with developer_intervention(dry_run=False) as audit_log:
            for row in reader:
                party_id = row["party_id"]
                address = row["address"].replace("\\r\\n", "\r\n")
                new_address = row["new_address"].replace("\\r\\n", "\r\n")
                additional_text = row["additional_text"]

                self.update_field_on_party(party_id, address, new_address, additional_text, audit_log)

    def update_field_on_party(self, party_id, address, new_address, additional_text, audit_log):
        party = Party.objects.get(id=party_id, address=address)

        audit_log(
            party,
            additional_text,
            {
                "address": {"new": new_address, "old": address},
            },
        )

        party.address = new_address
        party.save()
        self.stdout.write(f"Updated address for Party {party_id} from {address} to {new_address}.")
