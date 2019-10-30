from django.core.management import BaseCommand
from django.db import transaction

from static.letter_layouts.models import LetterLayout

layouts = {
    'licence': 'Licence',
    'siel': 'SIEL'
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
        for layout_id, layout_name in layouts.items():
            LetterLayout(id=layout_id,  name=layout_name).save()
            print("Seeded %s layout" % layout_name)

        self.stdout.write(self.style.SUCCESS(success_message))
