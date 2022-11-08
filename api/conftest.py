from django.core.management import call_command
from django.db.migrations.executor import MigrationExecutor
from django import db
from django.conf import settings

import re
import glob
from importlib import import_module

import pytest  # noqa
from django.conf import settings


def camelcase_to_underscore(string):
    """SRC: https://djangosnippets.org/snippets/585/"""
    return re.sub("(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))", "_\\1", string).lower().strip("_")


def collect_factories(rootpath):
    """
    Will collect (recursively) and return all factories found under given root path
    """
    factories_collected = {}  # <factory name> : <factory class>
    factory_files = glob.glob(f"{rootpath}/**/factories.py", recursive=True)

    for factory_file in factory_files:
        factory_module_path = factory_file.replace("/", ".").split(".py")[0]
        mod = import_module(factory_module_path)

        # Recognize factories by the *Factory suffix
        for resource_name in dir(mod):
            if not resource_name.endswith("Factory"):
                continue
            factory = getattr(mod, resource_name)
            if resource_name in factories_collected:
                # Just skip if it's the exact same factory
                if factory == factories_collected[resource_name]:
                    continue
                raise Exception(f"Factory with name '{resource_name}' already exists in another file")
            factories_collected[resource_name] = factory

    return factories_collected


# Create pytest fixture for each factory found in the project
#
# This allows us to directly use factories just like pytest/factoryboy
#
# Example:
#
#   class TestTeam():
#      def test_my_team(team_factory):
#          my_team = team_factory()
#
collected_factories = collect_factories("api")
fixture_names = []
for factory_name, factory in collected_factories.items():
    fixture_name = camelcase_to_underscore(factory_name)
    fixture_names.append(fixture_name)
    exec(  # nosec
        f"""
@pytest.fixture
def {fixture_name}(db):
    return collected_factories['{factory_name}']
         """
    )
if settings.DEBUG:
    for fixture_name in sorted(fixture_names):
        print(f"pytest.fixture: {fixture_name}")


@pytest.fixture()
def migration(transactional_db):
    """
    This fixture returns a helper object to test Django data migrations.
    The fixture returns an object with two methods;
     - `before` to initialize db to the state before the migration under test
     - `after` to execute the migration and bring db to the state after the
    migration. The methods return `old_apps` and `new_apps` respectively; these
    can be used to initiate the ORM models as in the migrations themselves.
    For example:
        def test_foo_set_to_bar(migration):
            old_apps = migration.before([('my_app', '0001_inital')])
            Foo = old_apps.get_model('my_app', 'foo')
            Foo.objects.create(bar=False)
            assert Foo.objects.count() == 1
            assert Foo.objects.filter(bar=False).count() == Foo.objects.count()
            # executing migration
            new_apps = migration.apply('my_app', '0002_set_foo_bar')
            Foo = new_apps.get_model('my_app', 'foo')
            assert Foo.objects.filter(bar=False).count() == 0
            assert Foo.objects.filter(bar=True).count() == Foo.objects.count()
    From: https://gist.github.com/asfaltboy/b3e6f9b5d95af8ba2cc46f2ba6eae5e2
    """

    class Migrator:
        def before(self, migrate_from):
            """Specify app and starting migration name as in:
            before(['app', '0001_before']) => app/migrations/0001_before.py
            """
            self.migrate_from = migrate_from
            self.executor = MigrationExecutor(db.connection)
            self.executor.migrate(self.migrate_from)
            self._old_apps = self.executor.loader.project_state(self.migrate_from).apps
            return self._old_apps

        def apply(self, app, migrate_to):
            """Migrate forwards to the "migrate_to" migration"""
            self.migrate_to = [(app, migrate_to)]
            self.executor.loader.build_graph()  # reload.
            self.executor.migrate(self.migrate_to)
            self._new_apps = self.executor.loader.project_state(self.migrate_to).apps
            return self._new_apps

    yield Migrator()
    call_command("migrate")


@pytest.fixture(autouse=True)
def setup(settings):
    settings.HAWK_AUTHENTICATION_ENABLED = False
