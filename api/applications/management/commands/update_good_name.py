import csv

from django.core.management.base import BaseCommand

from api.goods.models import Good
from api.support.helpers import developer_intervention


class Command(BaseCommand):
    help = "Update name for multiple goods from a CSV file"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=open, help="The path to the CSV file containing updates")

    def handle(self, *args, **kwargs):
        csv_file = kwargs["csv_file"]

        reader = csv.DictReader(csv_file, escapechar=None)
        with developer_intervention(dry_run=False) as audit_log:
            for row in reader:
                good_id = row["good_id"]
                name = row["name"]
                new_name = row["new_name"]
                additional_text = row["additional_text"]

                self.update_good_name(good_id, name, new_name, additional_text, audit_log)

    def update_good_name(self, good_id, name, new_name, additional_text, audit_log):
        good = Good.objects.get(id=good_id, name=name)

        audit_log(
            good,
            additional_text,
            {
                "name": {"new": new_name, "old": name},
            },
        )

        good.name = new_name
        good.save()
        self.stdout.write(f"Updated name for Good {good_id} from {name} to {new_name}.")
