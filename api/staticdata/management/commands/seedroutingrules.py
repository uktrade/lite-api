import uuid

from django.db import transaction

from api.cases.models import CaseStatus
from api.queues.models import Queue
from api.teams.models import Team
from api.staticdata.management.SeedCommand import SeedCommand
from api.workflow.routing_rules.models import RoutingRule


ROUTING_RULES_FILE = "lite_content/lite_api/routing_rules.csv"


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedroutingrules
    """

    help = "Seeds routing rules"
    info = "Seeding routing rules"
    seed_command = "seedroutingrules"

    @transaction.atomic
    def operation(self, *args, **options):
        if RoutingRule.objects.exists():
            self.stdout.write(self.style.WARNING("Routing rules already exist, skipping seeding"))
            return

        statuses = {status.status: status for status in CaseStatus.objects.all()}
        teams = {team.name: team for team in Team.objects.all()}
        queues = {queue.name: queue for queue in Queue.objects.all()}

        try:
            csv = self.read_csv(ROUTING_RULES_FILE)
        except FileNotFoundError:
            self.stdout.write(self.style.WARNING("Routing rules file does not exist, skipping seeding"))
            return

        for row in csv:
            for k, v in row.items():
                if not v:
                    row[k] = None
            row["id"] = uuid.uuid4()
            row["status"] = statuses[row["status"]]
            row["team"] = teams[row["team"]]
            row["queue"] = queues[row["queue"]]
            row["additional_rules"] = row["additional_rules"].split(",")

        self.update_or_create(RoutingRule, csv)
