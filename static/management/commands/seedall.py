from static.management.SeedCommand import SeedCommand

from static.management.commands import seedcontrollistentries, seedorgusers, seeddenialreasons, seedcountries, \
    seedgovuser, seedtestteam, seedpermissions


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
    def essential_seeding(*args, **options):
        seeddenialreasons.Command().handle(*args, **options)
        seedcountries.Command().handle(*args, **options)
        seedtestteam.Command().handle(*args, **options)
        seedpermissions.Command().handle(*args, **options)
        seedgovuser.Command().handle(*args, **options)

    @staticmethod
    def non_essential_seeding(*args, **options):
        seedcontrollistentries.Command().handle(*args, **options)
        seedorgusers.Command().handle(*args, **options)

    def operation(self, *args, **options):
        if options['essential']:
            self.essential_seeding(args, options)
        elif options['non_essential']:
            self.non_essential_seeding(args, options)
        else:
            self.essential_seeding(args, options)
            self.non_essential_seeding(args, options)
