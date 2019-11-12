from static.letter_layouts.models import LetterLayout
from static.management.SeedCommand import SeedCommandTest, SeedCommand

layouts = {
    'licence': 'Licence',
    'ecju': 'ECJU Letter'
}


class Command(SeedCommand):
    help = 'Creates template layouts'
    success = 'Successfully seeded layouts'
    seed_command = 'seedlayouts'

    def operation(self, *args, **options):
        """
        pipenv run ./manage.py seedlayouts
        """
        # Add layouts
        for layout_filename, layout_name in layouts.items():
            LetterLayout.objects.get_or_create(filename=layout_filename, name=layout_name)
            print("Seeded %s layout" % layout_name)


class SeedLayoutsTests(SeedCommandTest):
    def test_seed_layouts(self):
        self.seed_command(Command)
        self.assertTrue(LetterLayout.objects.count() == len(layouts))
