from django.db import transaction

from cases.enums import AdviceType
from api.staticdata.decisions.models import Decision
from api.staticdata.management.SeedCommand import SeedCommand


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedfinaldecisions
    """

    help = "Seeds final decisions"
    info = "Seeding final decisions"
    seed_command = "seedfinaldecisions"

    @transaction.atomic
    def operation(self, *args, **options):
        for name, id in AdviceType.ids.items():
            decision, created = Decision.objects.get_or_create(id=id, name=name)

            if created or decision.name != name:
                self.print_created_or_updated(Decision, {"id": id, "name": name}, is_created=created)
