import csv
from django.core.management.base import BaseCommand
from api.parties.models import Party
from api.users.models import BaseUser
from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from django.db import transaction


class Command(BaseCommand):
    help = "Update Name for multiple parties from a CSV file"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=open, help="The path to the CSV file containing updates")

    def handle(self, *args, **kwargs):
        csv_file = kwargs["csv_file"]

        reader = csv.DictReader(csv_file)
        with transaction.atomic():
            for row in reader:
                party_id = row["party_id"]
                name = row["name"].replace("\\r\\n", "\r\n")
                new_name = row["new_name"].replace("\\r\\n", "\r\n")
                additional_text = row["additional_text"]

                self.update_field_on_party(party_id, name, new_name, additional_text)

    def update_field_on_party(self, party_id, name, new_name, additional_text):
        party = Party.objects.get(id=party_id, name=name)
        system_user = BaseUser.objects.get(id="00000000-0000-0000-0000-000000000001")

        audit_trail_service.create(
            actor=system_user,
            verb=AuditType.DEVELOPER_INTERVENTION,
            target=party,
            payload={"name": {"new": new_name, "old": name}, "additional_text": additional_text},
        )

        party.name = new_name
        party.save()
        self.stdout.write(f"Updated name for Party {party_id} from {name} to {new_name}.")
