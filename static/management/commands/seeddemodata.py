from uuid import uuid4

from django.db import transaction, models

from static.management.SeedCommand import SeedCommand, SeedCommandTest

from flags.models import Flag
from queues.models import Queue
from teams.models import Team

FLAGS_FILE = "lite_content/lite_api/demo_flags.csv"
QUEUES_FILE = "lite_content/lite_api/demo_queues.csv"
TEAMS_FILE = "lite_content/lite_api/demo_teams.csv"


class Command(SeedCommand):
    """
    pipenv run ./manage.py seeddemodata
    """

    help = "Creates Teams, Queues and Flags for the purpose of demoing"
    info = "Seeding demo data"
    success = "Successfully seeded demo data"
    seed_command = "seeddemodata"

    @transaction.atomic
    def operation(self, *args, **options):
        teams = self.seed_teams()
        self.seed_queues(teams)
        self.seed_flags(teams)

    def seed_teams(self):
        teams_csv = self.read_csv(TEAMS_FILE)
        return self.create_team(Team, teams_csv)

    def seed_queues(self, team_ids):
        queues_csv = self.read_csv(QUEUES_FILE)
        self._create_queue_or_flag(Queue, queues_csv, team_ids)

    def seed_flags(self, team_ids):
        flags_csv = self.read_csv(FLAGS_FILE)
        self._create_queue_or_flag(Flag, flags_csv, team_ids)

    @staticmethod
    def create_team(model: models.Model, rows: list):
        teams = {}
        for row in rows:
            team = Team.objects.filter(name=row["name"])
            if not team.exists():
                team = model.objects.create(**row)
                print(f"CREATED {model.__name__}: {dict(row)}")
            else:
                team = team.first()
            teams[row["name"]] = team
        return teams

    @staticmethod
    def _create_queue_or_flag(model: models.Model, rows: list, teams):
        for row in rows:
            row["team"] = teams[row["team"]]
            obj = model.objects.filter(team_id=row["team"], name=row["name"])
            if not obj.exists():
                model.objects.create(**row)
                print(f"CREATED {model.__name__}: {dict(row)}")


class SeedDemoDataTests(SeedCommandTest):
    def test_seed_case_statuses(self):
        self.seed_command(Command)
        self.assertTrue(Flag.objects.count() == len(Command.read_csv(FLAGS_FILE)))
        self.assertTrue(Queue.objects.count() == len(Command.read_csv(QUEUES_FILE)))
        self.assertTrue(Team.objects.count() == len(Command.read_csv(TEAMS_FILE)))
