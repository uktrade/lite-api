from django.core.management import call_command

from django.conf import settings
from static.management.SeedCommand import SeedCommand

SEED_COMMANDS = {
    "Essential": [
        "seedcasetypes",
        "seedcasestatuses",
        "seedrolepermissions",
        "seedsystemuser",
        "seedadminteam",
        "seedinternalusers",
        "seedcontrollistentries",
        "seeddenialreasons",
        "seedcountries",
        "seedlayouts",
        "seedfinaldecisions",
        "seedflags",
        "seedf680clearancetypes",
    ],
    "Dev": ["seedinternaldemodata", "seedexporterusers"],
    "Tests": [
        "seedcasetypes",
        "seedcasestatuses",
        "seedrolepermissions",
        "seedsystemuser",
        "seedadminteam",
        "seedinternalusers",
        "seeddenialreasons",
        "seedcountries",
        "seedlayouts",
        "seedfinaldecisions",
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
    success = "SUCCESSFULLY EXECUTED ALL SEED OPERATIONS"
    failure = "EXECUTED ALL SEED OPERATIONS WITH FAILURES"

    def add_arguments(self, parser):
        parser.add_argument(
            "--essential", action="store_true", help="Executes: " + ", ".join(SEED_COMMANDS["Essential"]),
        )
        parser.add_argument(
            "--dev", action="store_true", help="Executes: " + ", ".join(SEED_COMMANDS["Dev"]),
        )

    @staticmethod
    def seed_list(commands):
        errors = []

        for command in commands:
            Command.print_separator()

            error = call_command(command, fail_on_error=False)
            if error:
                errors.append((command, error))

        return errors

    def operation(self, *args, **options):
        """
        pipenv run ./manage.py seedall --essential --dev

        essential & dev are optional params to only run certain seeding operations
        """
        errors = []

        if not options["essential"] and not options["dev"]:
            errors += self.seed_list(SEED_COMMANDS["Essential"])
            errors += self.seed_list(SEED_COMMANDS["Dev"])
        else:
            if options["essential"]:
                errors += self.seed_list(SEED_COMMANDS["Essential"])

            if options["dev"]:
                errors += self.seed_list(SEED_COMMANDS["Dev"])

        self.print_separator()

        if errors:
            error_messages = ""

            for error in errors:
                error_messages += f"\n\n{error[0]} -> {error[1]}"

            raise Exception(error_messages)

    @staticmethod
    def print_separator():
        if not settings.SUPPRESS_TEST_OUTPUT:
            print("=============================")
