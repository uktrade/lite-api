from abc import ABC

from django.core.management import BaseCommand


class SeedCommand(ABC, BaseCommand):
    """
    help and success message should be overridden
    with messages relevant to the operation
    """
    help = None
    success = None

    """
    operation should be overridden in child class
    with the code required to execute the seed operation
    """
    def operation(self, *args, **options):
        pass

    def handle(self, *args, **options):
        self.operation(*args, **options)
        self.stdout.write(self.style.SUCCESS(self.success))
