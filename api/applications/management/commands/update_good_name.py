import csv
from django.core.management.base import BaseCommand, CommandError
from api.goods.models import Good
from api.users.models import BaseUser
from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from django.db import transaction


class Command(BaseCommand):
    help = "Update name for multiple goods from a CSV file"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=open, help="The path to the CSV file containing updates")

    def handle(self, *args, **kwargs):
        csv_file = kwargs["csv_file"]

        reader = csv.DictReader(csv_file)
        for row in reader:
            good_id = row["good_id"]
            name = row["name"]
            new_name = row["new_name"]
            additional_text = row["additional_text"]

            self.update_good_name(good_id, name, new_name, additional_text)

    def update_good_name(self, good_id, name, new_name, additional_text):
        good = Good.objects.get(id=good_id)
        system_user = BaseUser.objects.get(id="00000000-0000-0000-0000-000000000001")

        with transaction.atomic():
            audit_trail_service.create(
                actor=system_user,
                verb=AuditType.DEVELOPER_INTERVENTION,
                target=good,
                payload={"name": {"new": new_name, "old": name}, "additional_text": additional_text},
            )

            if good.name == name:
                good.name = new_name
                good.save()
                self.stdout.write(f"Updated name for Good {good_id} from {name} to {new_name}.")
            else:
                raise CommandError("Current name does not match csv name, please check csv values")
