import re
import glob
from importlib import import_module

import pytest  # noqa
from django.conf import settings
from rest_framework.test import APIClient

from api.users.models import ExporterUser, GovUser, UserOrganisationRelationship
from api.users.libraries.user_to_token import user_to_token


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


# -------------------------- Clients ----------------------------


class LiteClient(APIClient):
    """
    APIClient from rest_framework with appropriate headers when we login()
    """

    def __init__(self, *args, **kwargs):
        self.headers = {}
        super().__init__(*args, **kwargs)

    def login(self, user, organisation=None):
        """
        Set headers appropriately for exporter and gov user

        If no organisation given for exporter, an existing one will be used
        """
        self.user = user  # just for easy reference so we can always see who we are logged-in as
        if isinstance(user, ExporterUser):

            # Re-use existing organisation if not explicitly given one
            if not organisation:
                try:
                    org_relation = UserOrganisationRelationship.objects.get(user=user)
                except UserOrganisationRelationship.DoesNotExist:
                    raise Exception("Exporter user must belong to an organisation to be able and login")
                organisation = org_relation.organisation

            # Use given organisation
            else:
                try:
                    UserOrganisationRelationship.objects.get(user=user, organisation=organisation)
                except UserOrganisationRelationship.DoesNotExist:
                    raise Exception(
                        "Missing UserOrganisationRelationship for given exporter_user and organisation. Create the relationship and try again."
                    )

            self.headers = {
                "HTTP_EXPORTER_USER_TOKEN": user_to_token(user.baseuser_ptr),
                "HTTP_ORGANISATION_ID": str(organisation.id),
            }

        elif isinstance(user, GovUser):
            if organisation:
                raise Exception("No organisation required for gov user")
            self.headers = {"HTTP_GOV_USER_TOKEN": user_to_token(user)}
        else:
            raise Exception(f"Unknown user type: {user}")

    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs, **self.headers)

    def post(self, *args, **kwargs):
        return super().post(*args, **kwargs, **self.headers)

    def put(self, *args, **kwargs):
        return super().put(*args, **kwargs, **self.headers)

    def patch(self, *args, **kwargs):
        return super().patch(*args, **kwargs, **self.headers)

    def delete(self, *args, **kwargs):
        return super().delete(*args, **kwargs, **self.headers)

    def head(self, *args, **kwargs):
        return super().head(*args, **kwargs, **self.headers)

    def options(self, *args, **kwargs):
        return super().options(*args, **kwargs, **self.headers)


@pytest.fixture
def exporter_client_with_standard_application(exporter_user_factory, standard_application_factory):
    """
    Return: A client logged-in as exporter and their application
    """
    exporter_user = exporter_user_factory()
    relation = UserOrganisationRelationship.objects.get(user=exporter_user)
    organisation = relation.organisation
    standard_application = standard_application_factory(organisation=organisation)
    client = LiteClient()
    client.login(exporter_user, organisation)
    return client, standard_application


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
