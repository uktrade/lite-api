from faker import Faker

from flags.models import Flag
from flags.tests.factories import FlagFactory
from goods.models import Good
from organisations.tests.providers import OrganisationProvider
from static.management.SeedCommand import SeedCommand
from teams.models import Team

faker = Faker()
faker.add_provider(OrganisationProvider)


class Command(SeedCommand):
    help = "Seeds data"
    info = "Seeding data"
    success = "Successfully completed action"
    seed_command = "seedfakeflag"

    def operation(self, *args, **options):
        while True:
            name = faker.word()

            while Flag.objects.filter(name=name).exists():
                name = faker.word()

            flag = FlagFactory(name=name, level="Destination", team=Team.objects.get(name="Admin"), priority=10)
            # for case in Good.objects.filter(status="verified").order_by("-created_at")[:25]:
            #     case.flags.add(flag)
            #     print(f"Created {flag.name} and added to {case.id}")
