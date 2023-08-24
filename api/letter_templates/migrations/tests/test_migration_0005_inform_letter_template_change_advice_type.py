import pytest
from django_test_migrations.contrib.unittest_case import MigratorTestCase


@pytest.mark.django_db()
class TestChangeInformLetterAdviceType(MigratorTestCase):

    migrate_from = ("letter_templates", "0004_inform_letter_template")
    migrate_to = ("letter_templates", "0005_inform_letter_template_change_advice_type")


    def test_migration_0005_inform_letter_template_change_advice_type(self):   
        

        LetterTemplate = self.old_state.apps.get_model("letter_templates", "LetterTemplate")
        ADVICETYPE_INFORM_ID = "00000000-0000-0000-0000-000000000007"

        # check template
        letter_template = LetterTemplate.objects.get(name="Inform letter")
        assert str(letter_template.decisions.all()[0].id) == ADVICETYPE_INFORM_ID



