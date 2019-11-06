from static.management.SeedCommand import SeedCommand

from static.management.commands import seedcontrollistentries, seedorgusers, seeddenialreasons, seedcountries, \
    seedgovuser


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedall
    """
    help = 'Executes all seed operations'
    success = 'All seed operations executed!'

    def operation(self, *args, **options):
        seedcontrollistentries.Command().handle(*args, **options)
        seedorgusers.Command().handle(*args, **options)
        seeddenialreasons.Command().handle(*args, **options)
        seedcountries.Command().handle(*args, **options)
        seedgovuser.Command().handle(*args, **options)
