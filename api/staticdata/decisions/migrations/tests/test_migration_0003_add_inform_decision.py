import pytest
from django_test_migrations.contrib.unittest_case import MigratorTestCase


@pytest.mark.django_db()
class TestAddInformDecision(MigratorTestCase):

    migrate_from = ("decisions", "0002_alter_decision_name")
    migrate_to = ("decisions", "0003_add_inform_decision")


    def test_migration_0003_test_add_inform_decision(self):   
        
        ADVICETYPE_INFORM_ID = "00000000-0000-0000-0000-000000000007"

        Decision = self.old_state.apps.get_model("decisions", "Decision")
        
        assert Decision.objects.get(id=ADVICETYPE_INFORM_ID)

    


