from django.core.management import call_command
from django.db import transaction

from static.management.SeedCommand import SeedCommand

SEED_COMMANDS = {
    "Essential": [
        "seedcasetypes",
        "seedcasestatuses",
        "seedrolepermissions",
        "seedcontrollistentries",
        "seeddenialreasons",
        "seedcountries",
        "seedlayouts",
        "seedteams",
        "seedflags",
        "seedf680clearancetypes",
        "seedadminuser",
    ],
    "Dev": ["seeddemodata", "seeddemousers"],
    "Tests": [
        "seedcasetypes",
        "seedcasestatuses",
        "seedrolepermissions",
        "seeddenialreasons",
        "seedcountries",
        "seedlayouts",
        "seedteams",
        "seedflags",
        "seedf680clearancetypes",
    ],
}


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedall
    """

    help = "executes all seed operations"
    info = "EXECUTING ALL SEED OPERATIONS"
    success = "ALL SEED OPERATIONS EXECUTED"

    def add_arguments(self, parser):
        parser.add_argument(
            "--essential", action="store_true", help="Executes: " + ", ".join(SEED_COMMANDS["Essential"]),
        )
        parser.add_argument(
            "--dev", action="store_true", help="Executes: " + ", ".join(SEED_COMMANDS["Dev"]),
        )

    @staticmethod
    def seed_list(commands):
        for command in commands:
            call_command(command)

    @transaction.atomic
    def operation(self, *args, **options):
        """
        pipenv run ./manage.py seedall [--essential] [--non-essential]

        essential & non-essential are optional params to only run seed certain tasks
        """
        if not options["essential"] and not options["dev"]:
            self.seed_list(SEED_COMMANDS["Essential"])
            self.seed_list(SEED_COMMANDS["Dev"])
        else:
            if options["essential"]:
                self.seed_list(SEED_COMMANDS["Essential"])

            if options["dev"]:
                self.seed_list(SEED_COMMANDS["Dev"])
