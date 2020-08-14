from django.db import IntegrityError
from faker import Faker

from api.conf.constants import Roles
from api.flags.enums import SystemFlags
from static.countries.models import Country
from api.users.models import ExporterUser, UserOrganisationRelationship

faker = Faker()


def generate_key_value_pair(key, choices):
    """
    Given a key from a list of choices, generate a key value pair
    :param key: A key from a list of choices, eg "in_review"
    :param choices: A list of tuples, matching the key with a display version of it
    :return: A key value pair of the key and its value, eg {"key": "in_review", "value": "In review"}
    """
    value = next(v for k, v in choices if k == key)
    return {"key": key, "value": value}


def generate_country_dict(country: Country):
    """
    Returns a dictionary representing a country, useful for comparison tests
    """
    return {"id": country.id, "name": country.name, "is_eu": country.is_eu, "type": country.type}


def create_exporter_users(organisation, quantity=1, role_id=Roles.EXPORTER_DEFAULT_ROLE_ID):
    users = []

    for i in range(quantity):
        user, created = ExporterUser.objects.get_or_create(email=faker.email())
        if created:
            user.first_name = faker.first_name()
            user.last_name = faker.last_name()
            user.save()
        UserOrganisationRelationship(user=user, organisation=organisation, role_id=role_id).save()
        users.append(user)

    return users


def is_not_verified_flag_set_on_good(good):
    flags_on_good = [str(id) for id in good.flags.values_list("id", flat=True)]
    return SystemFlags.GOOD_NOT_YET_VERIFIED_ID in flags_on_good


def node_by_id(items: list, id):
    """
    Finds a dictionary with the id provided
    """
    for item in items:
        if str(item["id"]) == str(id):
            return item

    raise KeyError(f"ID '{id}' not found in list")
