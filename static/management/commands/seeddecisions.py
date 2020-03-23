from django.db import transaction

from cases.enums import AdviceType
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
        for name, id in AdviceType.ids.items():
            _, created = Decision.objects.get_or_create(id=id, name=name)
            self.print_created_or_updated(Decision, {"id": id, "name": name}, is_created=created)
