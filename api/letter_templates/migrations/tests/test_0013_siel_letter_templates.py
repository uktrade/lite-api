import pytest
from django_test_migrations.contrib.unittest_case import MigratorTestCase

APPROVAL_LAYOUT_ID = "00000000-0000-0000-0000-000000000001"  # /PS-IGNORE
APPROVAL_LETTER_ID = "d159b195-9256-4a00-9bc8-1eb2cebfa1d2"
REFUSAL_LAYOUT_ID = "00000000-0000-0000-0000-000000000006"  # /PS-IGNORE
REFUSAL_LETTER_ID = "074d8a54-ee10-4dca-82ba-650460650342"
NLR_LAYOUT_ID = "00000000-0000-0000-0000-000000000003"
NLR_LETTER_ID = "d71c3cfc-a127-46b6-96c0-a435cdd63cdb"


@pytest.mark.django_db()
class TestSIELLetterTemplatesMigration(MigratorTestCase):
    migrate_from = ("letter_templates", "0012_oiel_letter_templates")
    migrate_to = ("letter_templates", "0013_siel_letter_templates")

    def test_siel_letter_templates(self):
        CASETYPE_SIEL_ID = "00000000-0000-0000-0000-000000000004"
        APPROVE_DECISION_ID = "00000000-0000-0000-0000-000000000001"
        REFUSE_DECISION_ID = "00000000-0000-0000-0000-000000000003"
        NLR_DECISION_ID = "00000000-0000-0000-0000-000000000004"

        LetterTemplates = self.new_state.apps.get_model("letter_templates", "LetterTemplate")

        approval_template = LetterTemplates.objects.get(name="SIEL template")
        refuse_template = LetterTemplates.objects.get(name="Refusal letter template")
        nlr_template = LetterTemplates.objects.get(name="No licence required letter template")

        assert str(approval_template.id) == APPROVAL_LETTER_ID
        assert str(approval_template.layout.name) == "SIEL"
        assert approval_template.case_types.filter(id=CASETYPE_SIEL_ID).exists()
        assert approval_template.decisions.filter(id=APPROVE_DECISION_ID).exists()

        assert str(refuse_template.id) == REFUSAL_LETTER_ID
        assert str(refuse_template.layout.name) == "Refusal Letter"
        assert refuse_template.case_types.filter(id=CASETYPE_SIEL_ID).exists()
        assert refuse_template.decisions.filter(id=REFUSE_DECISION_ID).exists()

        assert str(nlr_template.id) == NLR_LETTER_ID
        assert str(nlr_template.layout.name) == "No Licence Required Letter"
        assert nlr_template.case_types.filter(id=CASETYPE_SIEL_ID).exists()
        assert nlr_template.decisions.filter(id=NLR_DECISION_ID).exists()


@pytest.mark.django_db()
class TestSIELExistingLetterTemplatesMigration(MigratorTestCase):
    migrate_from = ("letter_templates", "0012_oiel_letter_templates")
    migrate_to = ("letter_templates", "0013_siel_letter_templates")

    def prepare(self):
        LetterLayout = self.old_state.apps.get_model("letter_layouts", "LetterLayout")
        LetterTemplates = self.old_state.apps.get_model("letter_templates", "LetterTemplate")
        # these are all get_or_create to allow for the tests to pass as expected
        siel_approval_layout, _ = LetterLayout.objects.get_or_create(
            id=APPROVAL_LAYOUT_ID, name="SIEL", filename="siel"
        )
        siel_refusal_layout, _ = LetterLayout.objects.get_or_create(
            id=REFUSAL_LAYOUT_ID, name="Refusal Letter", filename="refusal"
        )
        nlr_layout, _ = LetterLayout.objects.get_or_create(
            id=NLR_LAYOUT_ID,
            name="No Licence Required Letter",
            filename="nlr",
        )

        LetterTemplates.objects.get_or_create(
            id=APPROVAL_LETTER_ID,
            name="SIEL template",
            layout=siel_approval_layout,
            visible_to_exporter=True,
            include_digital_signature=True,
        )
        LetterTemplates.objects.get_or_create(
            id=REFUSAL_LETTER_ID,
            name="Refusal letter template",
            layout=siel_refusal_layout,
            visible_to_exporter=True,
            include_digital_signature=True,
        )
        LetterTemplates.objects.get_or_create(
            id=NLR_LETTER_ID,
            name="No licence required letter template",
            layout=nlr_layout,
            visible_to_exporter=True,
            include_digital_signature=True,
        )

    def test_siel_letter_templates_existing(self):

        LetterLayout = self.new_state.apps.get_model("letter_layouts", "LetterLayout")
        LetterTemplates = self.new_state.apps.get_model("letter_templates", "LetterTemplate")

        assert LetterLayout.objects.filter(name="SIEL").count() == 1
        assert LetterLayout.objects.filter(name="Refusal Letter").count() == 1
        assert LetterLayout.objects.filter(name="No Licence Required Letter").count() == 1

        assert LetterTemplates.objects.filter(name="SIEL template").count() == 1
        assert LetterTemplates.objects.filter(name="Refusal letter template").count() == 1
        assert LetterTemplates.objects.filter(name="No licence required letter template").count() == 1
