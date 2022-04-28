import csv

from io import StringIO

from django.conf import settings
from django.db import transaction, models

from api.flags.models import Flag
from api.queues.models import Queue
from api.staticdata.management.SeedCommand import SeedCommand
from api.teams.models import Team


def deserialize_csv_from_string(csv_string):
    with StringIO(csv_string) as fobj:
        return list(csv.DictReader(fobj))


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedinternaldemodata
    """

    help = "Seeds internal teams, queues and flags"
    info = "Seeding internal teams, queues and flags"
    seed_command = "seedinternaldemodata"

    @transaction.atomic
    def operation(self, *args, **options):
        teams = self.seed_teams()
        self.seed_queues(teams)
        self.seed_flags(teams)

    @classmethod
    def seed_teams(cls) -> dict:
        rows = deserialize_csv_from_string(settings.LITE_API_DEMO_TEAMS_CSV)
        teams = {}

        for row in rows:
            if not row.get("alias"):
                row["alias"] = None
            team = Team.objects.filter(name__iexact=row["name"])
            if not team.exists():
                team_id = Team.objects.create(**row).id
                cls.print_created_or_updated(Team, row, is_created=True)
            else:
                team_id = team.first().id
            teams[row["name"]] = str(team_id)

        return teams

    @classmethod
    def seed_queues(cls, team_ids):
        queues_csv = deserialize_csv_from_string(settings.LITE_API_DEMO_QUEUES_CSV)
        cls._create_queues_or_flags(Queue, queues_csv, team_ids, include_team_in_filter=True)

    @classmethod
    def seed_flags(cls, team_ids):
        flags_csv = deserialize_csv_from_string(settings.LITE_API_DEMO_FLAGS_CSV)
        cls._create_queues_or_flags(Flag, flags_csv, team_ids, include_team_in_filter=False)

    @classmethod
    def _create_queues_or_flags(cls, model: models.Model, rows: dict, teams: dict, include_team_in_filter: bool):
        for row in rows:
            if not row.get("alias"):
                row["alias"] = None
            team_name = row.pop("team_name")
            row["team_id"] = teams[team_name]
            filter = dict(name__iexact=row["name"])

            if include_team_in_filter:
                filter["team_id"] = row["team_id"]

            obj = model.objects.filter(**filter)

            if not obj.exists():
                model.objects.create(**row)
                data = dict(name=row["name"], team_name=team_name)
                cls.print_created_or_updated(model, data, is_created=True)
