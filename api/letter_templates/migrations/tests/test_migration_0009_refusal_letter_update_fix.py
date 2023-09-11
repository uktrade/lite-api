import pytest
from django_test_migrations.contrib.unittest_case import MigratorTestCase
from api.picklists.enums import PicklistType


@pytest.mark.django_db()
class TestChangeInformLetterAdviceType(MigratorTestCase):
    migrate_from = ("letter_templates", "0008_refusal_letter_update")
    migrate_to = ("letter_templates", "0009_refusal_letter_update_fix")

    def prepare(self):
        PicklistItem = self.old_state.apps.get_model("picklists", "PicklistItem")
        Team = self.old_state.apps.get_model("teams", "Team")

        admin = Team.objects.get(name="Admin")
        PicklistItem.objects.create(
            team=admin,
            name="Refusal letter content",
            type=PicklistType.LETTER_PARAGRAPH,
            text="Dear,\r\n\r\nHaving carefully considered your application, an export licence has been refused for the goods listed in the attached schedule. If you would like further information about the decision, please contact Jeanette Rosenberg at jeanette.rosenberg@trade.gov.uk, (tel: 07917 751 668).\r\n\r\nYou may appeal against this decision, but you must do so in writing within 28 calendar days of the date of this refusal letter. In doing so you must provide argument or information that was not available to us at the time of refusal, and which could materially affect the decision to refuse.\r\n\r\nAppeal letters should be sent by email to Colin Baker at colin.baker@trade.gov.uk. If you have any questions about the progress of your appeal, please contact Colin (tel: 07391 864 815).\r\n\r\nFor licence applications refused under the Strategic Export Licensing Criteria more information is available at:\r\nhttps://questions-statements.parliament.uk/written-statements/detail/2021-12-08/hcws449.\r\n\r\nYours sincerely,\r\n\r\nExport Control Joint Unit",
        )

        PicklistItem.objects.create(
            team=admin,
            name="Refusal letter content",
            type=PicklistType.LETTER_PARAGRAPH,
            text="Test 2",
        )

    def test_migration_0009_refusal_letter_update_fix(self):
        PicklistItem = self.new_state.apps.get_model("picklists", "PicklistItem")

        pick_list_queryset = PicklistItem.objects.filter(name="Refusal letter content")

        assert pick_list_queryset.count() == 1
        assert (
            "Dear {{ addressee.name }}\n\n**Application reference: {{ case_reference }}**\n**Your reference: {{ exporter_reference }}**\n\nWe have carefully considered your application and have refused an export licence for the products listed below. If you would like further information about the decision, please contact Jeanette Rosenberg at [jeanette.rosenberg@trade.gov.uk](mailto:jeanette.rosenberg@trade.gov.uk) or +44(0)7917 751668.\n\nYou may appeal this decision for up to 28 calendar days. The deadline to do so is {{ appeal_deadline }}. Send your appeal by email to Colin Baker at [colin.baker@trade.gov.uk](mailto:colin.baker@trade.gov.uk). You must provide any relevant information missing from your application that could affect our decision to refuse. \n\nWe cannot accept information about contractual losses, economic concerns, loss of staff or site closures as valid reasons for appeal.\n\nIf you have any questions about the progress of your appeal, please contact Colin Baker on +44(0)7391 864 815.\n\nYours sincerely\nMs Jeanette R Rosenberg \nHead of Licensing Unit \nExport Control Joint Unit"
            in pick_list_queryset.first().text.strip()
        )
