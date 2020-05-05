from django.core.management import call_command

from static.management.SeedCommand import SeedCommand

SEED_COMMANDS = {
    "Essential": [
        "seedcasetypes",
        "seedcasestatuses",
        "seedrolepermissions",
        "seedsystemuser",
        "seedinternaladminusers",
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
        "seedinternaladminusers",
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
            error = call_command(command, fail_on_error=False)

            if error:
                errors.append((command, error))

        return errors

    def operation(self, *args, **options):
        """
        pipenv run ./manage.py seedall --essential --dev

        essential & dev are optional params to only run seed certain tasks
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

        if errors:
            error_messages = ""

            for error in errors:
                error_messages += f"{error[0]}:\n{error[1]}\n\n"

            raise Exception(error_messages)
