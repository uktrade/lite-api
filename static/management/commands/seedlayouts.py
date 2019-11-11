from django.core.management import BaseCommand
from django.db import transaction

from static.letter_layouts.models import LetterLayout

layouts = {
    'licence': 'Licence',
    'ecju': 'ECJU Letter'
}
success_message = 'Layouts seeded successfully!'


class Command(BaseCommand):
    help = 'Creates template layouts'

    @transaction.atomic
    def handle(self, *args, **options):
        """
        pipenv run ./manage.py seedlayouts
        """
        # Clear all existing layouts
        LetterLayout.objects.all().delete()

        # Add layouts
        for layout_filename, layout_name in layouts.items():
            LetterLayout.objects.create(filename=layout_filename, name=layout_name)
            print("Seeded %s layout" % layout_name)

        self.stdout.write(self.style.SUCCESS(success_message))
