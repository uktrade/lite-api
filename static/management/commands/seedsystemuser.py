import json

from conf.settings import env
from django.db import transaction

from static.management.SeedCommand import SeedCommand
from users.models import BaseUser


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedsystemuser
    """

    help = "Seeds the LITE System user"
    info = "Seeding system user"
    success = "Successfully seeded system user"
    seed_command = "seedsystemuser"

    @transaction.atomic
    def operation(self, *args, **options):
        system_user = json.loads(env("SYSTEM_USER")) if env("SYSTEM_USER") else {}
        id = system_user["id"]
        first_name = system_user["first_name"]
        last_name = system_user["last_name"]

        defaults = {
            "id": id,
            "email": "N/A",
            "first_name": first_name,
            "last_name": last_name,
        }

        system_user, created = BaseUser.objects.get_or_create(id=id, defaults=defaults)

        if created or system_user.first_name != first_name or system_user.last_name != last_name:
            system_user.first_name = first_name
            system_user.last_name = last_name
            system_user.save()

            self.print_created_or_updated(BaseUser, defaults, created)
