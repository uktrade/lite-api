from django.core.management import BaseCommand
from django.db import connection


class Command(BaseCommand):
    """
    pipenv run ./manage.py cleardb
    """

    help = "Clear the database"

    def handle(self, *args, **options):
        print("\nDropping all database tables..\n")
        with connection.cursor() as cursor:
            sql = """DO $$ DECLARE r RECORD;BEGIN FOR r IN (SELECT tablename FROM
                  pg_catalog.pg_tables WHERE schemaname = 'public\' AND tableowner != 'rdsadmin')
                  LOOP EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';END LOOP;END $$;"""
            cursor.execute(sql)
