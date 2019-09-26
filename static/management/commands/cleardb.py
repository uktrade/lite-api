from django.core.management import BaseCommand
from subprocess import call as execute_bash_command
from django.apps import apps


class Command(BaseCommand):
    """
    pipenv run ./manage.py cleardb
    """

    def handle(self, *args, **options):
        execute_bash_command('./manage.py flush --no-input', shell=True)
        for app in apps.get_app_configs():
            if app.get_models():
                app_name_index = app.name.rfind('.')
                app_name = app.name[app_name_index+1:] if app_name_index > -1 else app.name
                execute_bash_command('./manage.py migrate ' + app_name.lower() + ' zero', shell=True)
