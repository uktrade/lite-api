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


# -------------------------- Fixtures ---------------------------


@pytest.fixture
def end_user(party_factory, party_on_application_factory):
    from api.parties.enums import PartyType

    return party_on_application_factory(party=party_factory(type=PartyType.END_USER))


@pytest.fixture
def standard_application(standard_application_factory):
    return standard_application_factory()


@pytest.fixture
def open_application(open_application_factory):
    return open_application_factory()
