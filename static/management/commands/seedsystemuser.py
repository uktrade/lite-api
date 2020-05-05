from json import loads as serialize

from django.db import transaction

from conf.settings import env
from static.management.SeedCommand import SeedCommand
from users.enums import UserType, SystemUser
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
        system_user = env("SYSTEM_USER")
        # The JSON representation of the variable is different on environments, so it needs to be parsed first
        system_user = system_user.replace("=>", ":")

        try:
            system_user = serialize(system_user)
        except ValueError:
            raise ValueError(
                f"SYSTEM_USER has incorrect format;"
                f'\nexpected format: {{"id": "", "email": "", "first_name": "", "last_name": ""}}'
                f"\nbut got: {system_user}"
            )

        # id = system_user["id"]
        id = 'system_user["id"]'
        first_name = system_user["first_name"]
        last_name = system_user["last_name"]

        defaults = {
            "id": id,
            "email": "N/A",
            "first_name": first_name,
            "last_name": last_name,
            "type": UserType.SYSTEM.value,
        }

        system_user, created = BaseUser.objects.get_or_create(id=id, defaults=defaults)

        if created or system_user.first_name != first_name or system_user.last_name != last_name:
            system_user.first_name = first_name
            system_user.last_name = last_name
            system_user.save()

            self.print_created_or_updated(BaseUser, defaults, created)
