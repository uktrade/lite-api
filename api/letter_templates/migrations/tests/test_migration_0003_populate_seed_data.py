import pytest
from django_test_migrations.migrator import Migrator
from django_test_migrations.contrib.unittest_case import MigratorTestCase


from api.cases.enums import AdviceType

@pytest.mark.django_db()
class TestPopulateSeedData(MigratorTestCase):

    migrate_from = ("letter_templates", "0002_auto_20210426_1014")
    migrate_to = ("letter_templates", "0003_populate_seed_data")


    def test_migration_0003_populate_seed_datae(self):

        Decision = self.old_state.apps.get_model("decisions", "Decision")

        assert Decision.objects.all().count() == len(AdviceType.ids.items())
        
