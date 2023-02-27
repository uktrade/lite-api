import pytest
from django_test_migrations.migrator import Migrator
from django_test_migrations.contrib.unittest_case import MigratorTestCase

from api.applications.tests.factories import SiteOnApplicationFactory


@pytest.mark.django_db()
class test_synchronise_onward_exported_fields(MigratorTestCase):

    migrate_from = ("applications", "0028_openapplication_goodstype_category")
    migrate_to = ("applications", "0029_standardapplication_contains_firearm")

    def prepare(self):
        standard_application = self.old_state.apps.get_model("applications", "StandardApplication")
        organisations = self.old_state.apps.get_model("organisations", "Organisation")
        # Please not it's not possible to use factory here since the model state has changed
        organisation = organisations.objects.create(name="test")

        # Surprisingly easy to create an application which is so old and has changed state
        # Please note that goods_categories no longer exists so this will fail
        # This would have worked closer to the time if  migration 0029_standardapplication_contains_firearm didn't
        # remove the field. Best practice is to first do a data migration test the migration and then removed the field
        # in a separate migration
        standard_application.objects.create(
            organisation=organisation, case_type_id=1, export_type="", goods_categories=["firearms"]
        )

        assert standard_application.objects.filter(goods_categories=["firearms"]).count() == 1

    def test_migration_0029_standardapplication_contains_firearm(self):
        """Run the test itself."""
        # After the initial migration is done, we can use the new model state:
        standard_application = self.new_state.apps.get_model("applications", "StandardApplication")
        assert standard_application.filter(goods_categories=None).count() == 1
