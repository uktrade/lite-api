from django.core.management import call_command

from static.management.SeedCommand import SeedCommand

ESSENTIAL = ['seedcontrollistentries', 'seeddenialreasons', 'seedcountries', 'seedtestteam', 'seedpermissions', 'seedcasestatuses']
NON_ESSENTIAL = ['seedgovuser', 'seedorgusers']
TESTS = ['seeddenialreasons', 'seedcountries', 'seedtestteam', 'seedpermissions', 'seedgovuser', 'seedcasestatuses']


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
        if options['essential']:
            self.seed_list(ESSENTIAL)
        elif options['non_essential']:
            self.seed_list(NON_ESSENTIAL)
        else:
            self.seed_list(ESSENTIAL)
            self.seed_list(NON_ESSENTIAL)
