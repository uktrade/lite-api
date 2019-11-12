from django.core.management import call_command

from static.management.SeedCommand import SeedCommand

ESSENTIAL = ['seedpermissions', 'seedcontrollistentries', 'seeddenialreasons', 'seedcountries', 'seedcasestatuses']
DEV = ['seedorgusers', 'seedgovuser']
TESTS = ['seedpermissions', 'seeddenialreasons', 'seedcountries', 'seedgovuser', 'seedgovuser', 'seedcasestatuses']


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedall
    """
    help = 'Executes all seed operations'
    success = 'All seed operations executed!'

    def add_arguments(self, parser):
        parser.add_argument('--essential', action='store_true')
        parser.add_argument('--non-essential', action='store_true')

    @staticmethod
    def seed_list(commands):
        for command in commands:
            call_command(command)

    def operation(self, *args, **options):
        """
        pipenv run ./manage.py seedall [--essential] [--non-essential]

        essential & non-essential are optional params to only run seed certain tasks
        """
        if options['essential']:
            self.seed_list(ESSENTIAL)
        elif options['non_essential']:
            self.seed_list(DEV)
        else:
            self.seed_list(ESSENTIAL)
            self.seed_list(DEV)
