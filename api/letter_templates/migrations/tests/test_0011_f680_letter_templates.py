import pytest
from django_test_migrations.contrib.unittest_case import MigratorTestCase

APPROVAL_LAYOUT_ID = "8627fbd5-062f-4573-9bdd-b1d80bd8c6bb"  # /PS-IGNORE
REFUSAL_LAYOUT_ID = "af455bdb-3fa4-41b5-9ff5-ca17d9f94828"  # /PS-IGNORE
APPROVAL_LETTER_ID = "68a17258-af0f-429e-922d-25945979fa6d"
REFUSAL_LETTER_ID = "218ed82f-eedb-41bb-9492-ab05b6d04e6f"


@pytest.mark.django_db()
class TestF680LetterTemplatesMigration(MigratorTestCase):
    migrate_from = ("letter_templates", "0010_refusal_letter_picklist_update_team_ownership")
    migrate_to = ("letter_templates", "0011_f680_letter_templates")

    def test_f680_letter_templates(self):
        CASETYPE_F680_ID = "00000000-0000-0000-0000-000000000007"
        APPROVE_DECISION_ID = "00000000-0000-0000-0000-000000000001"
        REFUSE_DECISION_ID = "00000000-0000-0000-0000-000000000003"

        LetterTemplates = self.new_state.apps.get_model("letter_templates", "LetterTemplate")

        approval_template = LetterTemplates.objects.get(name="F680 Approval")
        refuse_template = LetterTemplates.objects.get(name="F680 Refusal")

        assert str(approval_template.id) == APPROVAL_LETTER_ID
        assert str(approval_template.layout.name) == "F680 Approval"
        assert approval_template.case_types.filter(id=CASETYPE_F680_ID).exists()
        assert approval_template.decisions.filter(id=APPROVE_DECISION_ID).exists()

        assert str(refuse_template.id) == REFUSAL_LETTER_ID
        assert str(refuse_template.layout.name) == "F680 Refusal"
        assert refuse_template.case_types.filter(id=CASETYPE_F680_ID).exists()
        assert refuse_template.decisions.filter(id=REFUSE_DECISION_ID).exists()


@pytest.mark.django_db()
class TestF680ExistingLetterTemplatesMigration(MigratorTestCase):
    migrate_from = ("letter_templates", "0010_refusal_letter_picklist_update_team_ownership")
    migrate_to = ("letter_templates", "0011_f680_letter_templates")

    def prepare(self):
        LetterLayout = self.old_state.apps.get_model("letter_layouts", "LetterLayout")
        LetterTemplates = self.old_state.apps.get_model("letter_templates", "LetterTemplate")
        f680_approval_layout = LetterLayout.objects.create(
            id=APPROVAL_LAYOUT_ID, name="F680 Approval", filename="f680_approval"
        )
        f680_refusal_layout = LetterLayout.objects.create(
            id=REFUSAL_LAYOUT_ID, name="F680 Refusal", filename="f680_refusal"
        )

        LetterTemplates.objects.create(
            id=APPROVAL_LETTER_ID,
            name="F680 Approval",
            layout=f680_approval_layout,
            visible_to_exporter=True,
            include_digital_signature=True,
        )
        LetterTemplates.objects.create(
            id=REFUSAL_LETTER_ID,
            name="F680 Refusal",
            layout=f680_refusal_layout,
            visible_to_exporter=True,
            include_digital_signature=True,
        )

    def test_f680_letter_templates_existing(self):

        LetterLayout = self.new_state.apps.get_model("letter_layouts", "LetterLayout")
        LetterTemplates = self.new_state.apps.get_model("letter_templates", "LetterTemplate")

        assert LetterLayout.objects.filter(name="F680 Approval").count() == 1
        assert LetterLayout.objects.filter(name="F680 Refusal").count() == 1
        assert LetterTemplates.objects.filter(name="F680 Approval").count() == 1
        assert LetterTemplates.objects.filter(name="F680 Refusal").count() == 1
