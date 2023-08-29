import pytest
from django_test_migrations.migrator import Migrator
from django_test_migrations.contrib.unittest_case import MigratorTestCase

from lite_routing.routing_rules_internal.enums import FlagsEnum, FlaggingRulesEnum, QueuesEnum, RoutingRulesEnum


@pytest.mark.django_db()
class TestRemoveLUCountersignFlags(MigratorTestCase):

    migrate_from = ("countries", "0003_add_nir")
    migrate_to = ("countries", "0004_remove_lu_countersign_flags")

    def prepare(self):
        """Prepare some data before the migration."""
        Country = self.old_state.apps.get_model("countries", "Country")
        Flag = self.old_state.apps.get_model("flags", "Flag")

        lu_counter_flag = Flag.objects.get(id=FlagsEnum.LU_COUNTER_REQUIRED)
        lu_senior_counter_flag = Flag.objects.get(id=FlagsEnum.LU_SENIOR_MANAGER_CHECK_REQUIRED)

        country_1 = Country.objects.create(id="CountryA", name="Country A", is_eu=False)
        country_1.flags.add(lu_counter_flag)

        country_2 = Country.objects.create(id="CountryB", name="Country B", is_eu=False)
        country_2.flags.add(lu_senior_counter_flag)

        country_3 = Country.objects.create(id="CountryC", name="Country C", is_eu=False)
        country_3.flags.add(lu_counter_flag, lu_senior_counter_flag)

    def test_migration_0004_remove_lu_countersign_flags(self):
        Country = self.new_state.apps.get_model("countries", "Country")

        country_1 = Country.objects.get(name="Country A")
        assert country_1.flags.all().count() == 0

        country_2 = Country.objects.get(name="Country B")
        assert country_2.flags.all().count() == 0

        country_3 = Country.objects.get(name="Country C")
        assert country_3.flags.all().count() == 0
