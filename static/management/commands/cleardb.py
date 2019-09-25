from django.core.management import BaseCommand
from subprocess import call as execute_bash_command, PIPE


class Command(BaseCommand):
    """
    pipenv run ./manage.py cleardb
    """

    def handle(self, *args, **options):
        command_statement = 'echo "DROP SCHEMA public CASCADE;CREATE SCHEMA public;" | pipenv run ./manage.py dbshell'
        print('\n`' + command_statement + '`\n')
        execute_bash_command(command_statement, stdin=PIPE, shell=True)
