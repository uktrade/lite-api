import pytest
from django_test_migrations.migrator import Migrator
from django_test_migrations.contrib.unittest_case import MigratorTestCase


@pytest.mark.django_db()
class TestUserPendingField(MigratorTestCase):

    migrate_from = ("users", "0004_baseuser_pending")
    migrate_to = ("users", "0005_value_for_pending_field")

    def prepare(self):
        base_user = self.old_state.apps.get_model("users", "BaseUser")
        base_user.objects.create(first_name="joe", email="test@1231.test.com")  # /PS-IGNORE
        base_user.objects.create(first_name="", email="test@1232.test.com")  # /PS-IGNORE
        base_user.objects.create(first_name="", last_name="", email="test@124.test.com")  # /PS-IGNORE
        base_user.objects.create(first_name="", last_name="blogs", email="test@125.test.com")  # /PS-IGNORE
        base_user.objects.create(last_name="test", email="test@126.test.com")  # /PS-IGNORE

    def test_migration_0004_baseuser_pending(self):
        base_user = self.new_state.apps.get_model("users", "BaseUser")
        assert base_user.objects.filter(pending=True).count() == 4
        assert base_user.objects.filter(first_name="").first().pending is True
        assert base_user.objects.filter(first_name="joe").first().pending is False
