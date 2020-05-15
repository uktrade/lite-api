import csv
from abc import ABC
from io import StringIO

from django.core.management import BaseCommand, call_command
from django.db import transaction, models, IntegrityError
from django.db.models import QuerySet
from django.test import TestCase

from conf import settings


class SeedCommand(ABC, BaseCommand):
    """
    Help and Success message should be overridden
    with messages relevant to the operation
    """

    help: str = ""
    info: str = ""
    success: str = "Successfully executed seed operation"
    failure: str = "Failed to execute seed operation"
    seed_command: str = ""
    fail_on_error: bool = True

    def add_arguments(self, parser):
        parser.add_argument("--fail-on-error", help="Exit if any errors are encountered", type=bool)

    def handle(self, *args, **options):
        if "fail_on_error" in options:
            self.fail_on_error = options["fail_on_error"]

        if not settings.SUPPRESS_TEST_OUTPUT:
            self.stdout.write(self.style.WARNING(f"{self.info}\n\n"))

        try:
            self.operation(*args, **options)
        except Exception as error:  # noqa
            self.stdout.write(self.style.ERROR(f"\n{self.failure}\n"))
            error_message = f"{type(error).__name__}: {error}"
            if self.fail_on_error:
                print(error_message)
                exit(1)
            return error_message

        if not settings.SUPPRESS_TEST_OUTPUT:
            self.stdout.write(self.style.SUCCESS(f"\n\n{self.success}"))

    @transaction.atomic
    def operation(self, *args, **options):
        """
        operation should be overridden in child class
        with the code required to execute the seed operation
        """
        pass

    @staticmethod
    def read_csv(filename: str):
        """
        Takes a given csv filename and reads it into a list of dictionaries
        where the headers are used as keys and rows as value. For example
        a csv with two headers 'id' and 'name' would iterate through all rows
        in the csv producing {'id': ID, 'name': Name} for each row.
        :param filename: filename of csv
        :return: list of dict objects containing csv properties
        """
        with open(filename, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            return list(reader)

    @staticmethod
    def update_or_create(model: models.Model, rows: list):
        """
        Takes a list of dicts with an id field and other properties applicable
        to a given model. If an object with the given id exists, it will update all
        the fields to match what is given. If it does not exist a new entry will be created
        :param model: A given Django model to populate
        :param rows: A list of dictionaries (csv entries) to populate to the model
        """
        for row in rows:
            obj_id = row["id"]
            obj = model.objects.filter(id=obj_id)
            if not obj.exists():
                model.objects.create(**row)
                if not settings.SUPPRESS_TEST_OUTPUT:
                    print(f"CREATED {model.__name__}: {dict(row)}")
            else:
                SeedCommand.update_if_not_equal(obj, row)

    @staticmethod
    def update_if_not_equal(obj: QuerySet, row: dict):
        # Can not delete the "id" key-value from `rows` as it will manipulate the data which is later used in
        # `delete_unused_objects`
        attributes = {k: v for k, v in row.items() if k != "id"}
        obj = obj.exclude(**attributes)
        if obj.exists():
            obj.update(**attributes)
            if not settings.SUPPRESS_TEST_OUTPUT:
                print(f"UPDATED {obj.model.__name__}: {dict(row)}")

    @staticmethod
    def delete_unused_objects(model: models.Model, rows: list):
        """
        Takes a list of dicts with an id field and checks that no other
        records exist other than this given list
        :param model: A given Django model to check
        :param rows: A list of dictionaries (csv entries) to extract ID's from for checking
        """
        ids = [row["id"] for row in rows]
        for obj in model.objects.all():
            id = str(obj.id)
            if id not in ids:
                try:
                    obj.delete()
                    if not settings.SUPPRESS_TEST_OUTPUT:
                        print(f"Unused object deleted {id} from {model.__name__}")
                except IntegrityError:
                    if not settings.SUPPRESS_TEST_OUTPUT:
                        print(f"Object {id} could not be deleted due to foreign key constraint")

    @staticmethod
    def print_created_or_updated(obj, data, is_created: bool):
        if not settings.SUPPRESS_TEST_OUTPUT:
            created_or_updated = "CREATED" if is_created else "UPDATED"
            print(f"{created_or_updated} {obj.__name__}: {dict(data)}")


class SeedCommandTest(TestCase):
    """
    Default test class to be extended to test seed operations
    """

    def seed_command(self, seed_class):
        out = StringIO()
        call_command(seed_class.seed_command, stdout=out)
        if not settings.SUPPRESS_TEST_OUTPUT:
            self.assertIn(seed_class.success, out.getvalue())
