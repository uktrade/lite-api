from django.db import transaction

from conf import settings
from static.decisions.enums import Decisions
from static.decisions.models import Decision
from static.management.SeedCommand import SeedCommand


class Command(SeedCommand):
    """
    pipenv run ./manage.py seeddecisions
    """

    help = "Seeds all Final decisions"
    info = "Seeding Final decisions"
    success = "Successfully seeded Final decisions"
    seed_command = "seeddecisions"

    @transaction.atomic
    def operation(self, *args, **options):
        for id, name in Decisions.data.items():
            _, created = Decision.objects.get_or_create(id=id, name=name)
            if not settings.SUPPRESS_TEST_OUTPUT:
                if created:
                    print(f"CREATED Decision: {name}")
                else:
                    print(f"UPDATED Decision: {name}")
