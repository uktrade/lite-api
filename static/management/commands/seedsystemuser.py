from django.db import transaction

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
        defaults = {
            "id": SystemUser.id,
            "email": "N/A",
            "first_name": SystemUser.first_name,
            "last_name": SystemUser.last_name,
            "type": UserType.SYSTEM,
        }

        system_user, created = BaseUser.objects.get_or_create(id=SystemUser.id, defaults=defaults)

        if created or system_user.first_name != SystemUser.first_name or system_user.last_name != SystemUser.last_name:
            system_user.first_name = SystemUser.first_name
            system_user.last_name = SystemUser.last_name
            system_user.save()

            self.print_created_or_updated(BaseUser, defaults, created)
