from django.core.management import BaseCommand
from subprocess import call as execute_bash_command
from django.apps import apps
from django.db import connection


class Command(BaseCommand):
    """
    pipenv run ./manage.py cleardb
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--safe',
            help='String representing if we should safely reverse migrations or purge all tables',
            type=str
        )

    def handle(self, *args, **options):
        if not options['safe'] or options['safe'] != 'False':
            print('\nSafely dropping all database tables..\n')
            execute_bash_command('./manage.py flush --no-input', shell=True)
            for app in apps.get_app_configs():
                if app.get_models():
                    app_name_index = app.name.rfind('.')
                    app_name = app.name[app_name_index + 1:] if app_name_index > -1 else app.name
                    execute_bash_command('./manage.py migrate ' + app_name.lower() + ' zero', shell=True)
        else:
            print('\nForcefully dropping all database tables..\n')
            with connection.cursor() as cursor:
                sql = """DO $$ DECLARE r RECORD;BEGIN FOR r IN (SELECT tablename FROM 
                      pg_catalog.pg_tables WHERE schemaname = 'public\' AND tableowner != 'rdsadmin') 
                      LOOP EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';END LOOP;END $$;"""
                cursor.execute(sql)
