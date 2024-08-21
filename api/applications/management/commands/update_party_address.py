import csv
from django.core.management.base import BaseCommand
from api.parties.models import Party
from api.users.models import BaseUser
from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType


class Command(BaseCommand):
    help = "Update address for multiple parties from a CSV file"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=open, help="The path to the CSV file containing updates")

    def handle(self, *args, **kwargs):
        csv_file = kwargs["csv_file"]

        reader = csv.DictReader(csv_file)
        for row in reader:
            party_id = row["party_id"]
            address = row["address"]
            new_address = row["new_address"]

            self.update_field_on_party(party_id, address, new_address)

    def update_field_on_party(self, party_id, address, new_address):
        party = Party.objects.get(id=party_id)
        system_user = BaseUser.objects.get(id="00000000-0000-0000-0000-000000000001")

        audit_trail_service.create(
            actor=system_user,
            verb=AuditType.DEVELOPER_INTERVENTION,
            target=party,
            payload={
                "address": {"new": new_address, "old": address},
            },
        )

        assert party.address == address
        party.address = new_address
        party.save()
        self.stdout.write(f"Updated address for Party {party_id} from {address} to {new_address}.")
