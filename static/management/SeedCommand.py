import csv
from abc import ABC
from io import StringIO

from django.core.management import BaseCommand, call_command
from django.db import transaction
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
    def read_csv(filename):
        with open(filename, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            next(reader)  # skip the headers
            return list(reader)


class SeedCommandTest(TestCase):
    """
    Default test class to be extended to test seed operations
    """
    def seed_command(self, seed_class):
        out = StringIO()
        call_command(seed_class.seed_command, stdout=out)
        self.assertIn(seed_class.success, out.getvalue())
