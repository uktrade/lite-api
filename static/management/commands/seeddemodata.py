from django.db import transaction, models

from addresses.models import Address
from organisations.enums import OrganisationType
from organisations.models import Site, Organisation
from static.countries.helpers import get_country
from static.countries.models import Country
from static.management.SeedCommand import SeedCommand

from flags.models import Flag
from queues.models import Queue
from teams.models import Team

FLAGS_FILE = "lite_content/lite_api/demo_flags.csv"
QUEUES_FILE = "lite_content/lite_api/demo_queues.csv"
TEAMS_FILE = "lite_content/lite_api/demo_teams.csv"

DEFAULT_DEMO_ORG_NAME = "Archway Communications"
DEFAULT_DEMO_HMRC_ORG_NAME = "HMRC office at Battersea heliport"

ORGANISATIONS = [
    {"name": DEFAULT_DEMO_ORG_NAME, "type": OrganisationType.COMMERCIAL, "reg_no": "09876543"},
    {"name": DEFAULT_DEMO_HMRC_ORG_NAME, "type": OrganisationType.HMRC, "reg_no": "75863840"},
]


class Command(SeedCommand):
    """
    pipenv run ./manage.py seeddemodata
    """

    help = "Seeds demo teams, queues, flags and organisations"
    info = "Seeding demo teams, queues, flags and organisation"
    success = "Successfully seeded demo teams, queues, flags and organisation"
    seed_command = "seeddemodata"

    @transaction.atomic
    def operation(self, *args, **options):
        assert Country.objects.count(), "Countries must be seeded first!"

        teams = self.seed_teams()
        self.seed_queues(teams)
        self.seed_flags(teams)
        self.seed_organisations()

    @classmethod
    def seed_teams(cls) -> dict:
        rows = cls.read_csv(TEAMS_FILE)
        teams = {}

        for row in rows:
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
        queues_csv = cls.read_csv(QUEUES_FILE)
        cls._create_queues_or_flags(Queue, queues_csv, team_ids, include_team_in_filter=True)

    @classmethod
    def seed_flags(cls, team_ids):
        flags_csv = cls.read_csv(FLAGS_FILE)
        cls._create_queues_or_flags(Flag, flags_csv, team_ids, include_team_in_filter=False)

    @classmethod
    def seed_organisations(cls):
        for organisation in ORGANISATIONS:
            cls._create_organisation(organisation)

    @classmethod
    def _create_organisation(cls, org):
        organisation, _ = Organisation.objects.get_or_create(
            name=org["name"],
            type=org["type"],
            eori_number="1234567890AAA",
            sic_number="2345",
            vat_number="GB1234567",
            registration_number=org["reg_no"],
        )

        address, _ = Address.objects.get_or_create(
            address_line_1="42 Question Road",
            address_line_2="",
            country=get_country("GB"),
            city="London",
            region="London",
            postcode="Islington",
        )

        site, _ = Site.objects.get_or_create(name="Headquarters", organisation=organisation, address=address)
        organisation.primary_site = site
        organisation.save()

    @classmethod
    def _create_queues_or_flags(cls, model: models.Model, rows: dict, teams: dict, include_team_in_filter: bool):
        for row in rows:
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
