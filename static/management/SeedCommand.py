import csv
from abc import ABC
from io import StringIO

from django.core.management import BaseCommand, call_command
from django.db import transaction, models
from django.test import TestCase


class SeedCommand(ABC, BaseCommand):
    """
    Help and Success message should be overridden
    with messages relevant to the operation
    """

    help = None
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
        self.operation(*args, **options)
        self.stdout.write(self.style.SUCCESS(self.success))

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
            obj = model.objects.filter(id=row["id"])
            if obj.exists():
                obj.update(**row)
            else:
                model.objects.create(**row)


class SeedCommandTest(TestCase):
    """
    Default test class to be extended to test seed operations
    """

    def seed_command(self, seed_class):
        out = StringIO()
        call_command(seed_class.seed_command, stdout=out)
        self.assertIn(seed_class.success, out.getvalue())
