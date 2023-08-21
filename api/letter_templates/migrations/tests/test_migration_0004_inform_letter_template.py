import pytest
from django_test_migrations.migrator import Migrator
from django_test_migrations.contrib.unittest_case import MigratorTestCase



@pytest.mark.django_db()
class TestPopulateInformLetter(MigratorTestCase):

    migrate_from = ("letter_templates", "0003_populate_seed_data")
    migrate_to = ("letter_templates", "0004_inform_letter_template")


    def test_migration_0003_inform_letter_template(self):   
        

        LetterLayout = self.old_state.apps.get_model("letter_layouts", "LetterLayout")
        LetterTemplate = self.old_state.apps.get_model("letter_templates", "LetterTemplate")
        

        # check letter layout
        letter_layout = LetterLayout.objects.filter(name='Inform Letter')
        assert letter_layout.count() == 1

        # check template
        letter_template_query = LetterTemplate.objects.filter(name="Inform letter")
        assert letter_template_query.count() == 1
        letter_template = letter_template_query[0]
        
        assert letter_template.name
        assert letter_template.letter_paragraphs.count() == 3
        assert letter_template.decisions.count() == 1

        