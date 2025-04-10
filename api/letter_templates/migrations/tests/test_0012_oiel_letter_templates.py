import pytest
from django_test_migrations.contrib.unittest_case import MigratorTestCase

APPROVAL_LAYOUT_ID = "01353fba-906e-4199-ab18-5f1768a5f736"  # /PS-IGNORE
REFUSAL_LAYOUT_ID = "dccea004-99cc-4d16-b6f1-16f50d9cc82e"  # /PS-IGNORE
APPROVAL_LETTER_ID = "81b0c09e-aa96-4590-9393-e1fa09352bb4"
REFUSAL_LETTER_ID = "b9869e62-547c-4792-b374-c718c3493115"


@pytest.mark.django_db()
class TestOIELLetterTemplatesMigration(MigratorTestCase):
    migrate_from = ("letter_templates", "0011_f680_letter_templates")
    migrate_to = ("letter_templates", "0012_oiel_letter_templates")

    def test_oiel_letter_templates(self):
        CASETYPE_OIEL_ID = "00000000-0000-0000-0000-000000000001"
        APPROVE_DECISION_ID = "00000000-0000-0000-0000-000000000001"
        REFUSE_DECISION_ID = "00000000-0000-0000-0000-000000000003"

        LetterTemplates = self.new_state.apps.get_model("letter_templates", "LetterTemplate")

        approval_template = LetterTemplates.objects.get(name="OIEL Approval")
        refuse_template = LetterTemplates.objects.get(name="OIEL Refusal")

        assert str(approval_template.id) == APPROVAL_LETTER_ID
        assert str(approval_template.layout.name) == "OIEL Approval"
        assert approval_template.case_types.filter(id=CASETYPE_OIEL_ID).exists()
        assert approval_template.decisions.filter(id=APPROVE_DECISION_ID).exists()

        assert str(refuse_template.id) == REFUSAL_LETTER_ID
        assert str(refuse_template.layout.name) == "OIEL Refusal"
        assert refuse_template.case_types.filter(id=CASETYPE_OIEL_ID).exists()
        assert refuse_template.decisions.filter(id=REFUSE_DECISION_ID).exists()


@pytest.mark.django_db()
class TestOIELExistingLetterTemplatesMigration(MigratorTestCase):
    migrate_from = ("letter_templates", "0011_f680_letter_templates")
    migrate_to = ("letter_templates", "0012_oiel_letter_templates")

    def prepare(self):
        LetterLayout = self.old_state.apps.get_model("letter_layouts", "LetterLayout")
        LetterTemplates = self.old_state.apps.get_model("letter_templates", "LetterTemplate")
        oiel_approval_layout = LetterLayout.objects.create(
            id=APPROVAL_LAYOUT_ID, name="OIEL Approval", filename="oiel_approval"
        )
        oiel_refusal_layout = LetterLayout.objects.create(
            id=REFUSAL_LAYOUT_ID, name="OIEL Refusal", filename="oiel_refusal"
        )

        LetterTemplates.objects.create(
            id=APPROVAL_LETTER_ID,
            name="OIEL Approval",
            layout=oiel_approval_layout,
            visible_to_exporter=True,
            include_digital_signature=True,
        )
        LetterTemplates.objects.create(
            id=REFUSAL_LETTER_ID,
            name="OIEL Refusal",
            layout=oiel_refusal_layout,
            visible_to_exporter=True,
            include_digital_signature=True,
        )

    def test_oiel_letter_templates_existing(self):

        LetterLayout = self.new_state.apps.get_model("letter_layouts", "LetterLayout")
        LetterTemplates = self.new_state.apps.get_model("letter_templates", "LetterTemplate")

        assert LetterLayout.objects.filter(name="OIEL Approval").count() == 1
        assert LetterLayout.objects.filter(name="OIEL Refusal").count() == 1
        assert LetterTemplates.objects.filter(name="OIEL Approval").count() == 1
        assert LetterTemplates.objects.filter(name="OIEL Refusal").count() == 1
