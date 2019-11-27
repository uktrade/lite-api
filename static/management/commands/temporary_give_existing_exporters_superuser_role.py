from django.db import transaction

from static.management.SeedCommand import SeedCommand
from static.management.commands.seedrolepermissions import EX_SUPER_USER_ROLE_ID
from users.enums import UserStatuses
from users.models import UserOrganisationRelationship, Role


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedpermissions
    """

    help = "Seeds permissions"
    info = "Seeding permissions"
    success = "Successfully seeded permissions"
    seed_command = "temporary_give_existing_exporters_superuser_role"

    @transaction.atomic
    def operation(self, *args, **options):
        super_role = Role.objects.get(id=EX_SUPER_USER_ROLE_ID)
        for uor in UserOrganisationRelationship.objects.filter(status=UserStatuses.ACTIVE):
            uor.role = super_role
            uor.save()
