import csv
from abc import ABC
from io import StringIO

from django.core.management import BaseCommand, call_command
from django.db import transaction, models, IntegrityError
from django.db.models import QuerySet
from django.test import TestCase


class SeedCommand(ABC, BaseCommand):
    """
    Help and Success message should be overridden
    with messages relevant to the operation
    """

    help = None
    info = None
    success = None
    seed_command = None

    """
    operation should be overridden in child class
    with the code required to execute the seed operation
    """

    @transaction.atomic
    def operation(self, *args, **options):
        pass

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(f"\n=============================\n{self.info}\n=============================\n")
        )
        try:
            self.operation(*args, **options)
        except Exception as error:  # noqa
            self.stdout.write(self.style.ERROR(error.message if hasattr(error, "message") else error))
            return
        self.stdout.write(self.style.SUCCESS(f"\n{self.success}\n"))

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
                print(f"CREATED: {dict(row)}")
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
            print(f"UPDATED: {dict(row)}")

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
                    print(f"Unused object deleted {id} from {model.__name__}")
                except IntegrityError:
                    print(f"Object {id} could not be deleted due to foreign key constraint")


class SeedCommandTest(TestCase):
    """
    Default test class to be extended to test seed operations
    """

    def seed_command(self, seed_class):
        out = StringIO()
        call_command(seed_class.seed_command, stdout=out)
        self.assertIn(seed_class.success, out.getvalue())
