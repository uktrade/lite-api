from static.management.SeedCommand import SeedCommand

from static.management.commands import seedcontrollistentries, seedorgusers


class Command(SeedCommand):
    """
    pipenv run ./manage.py seedall
    """
    help = 'Executes all seed operations'
    success = 'All seed opertations executed!'

    def operation(self, *args, **options):
        seedcontrollistentries.Command().operation(*args, **options)
        seedorgusers.Command().operation(*args, **options)
