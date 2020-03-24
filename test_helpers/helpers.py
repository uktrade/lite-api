from faker import Faker

from flags.enums import SystemFlags
from static.countries.models import Country
from users.models import ExporterUser, UserOrganisationRelationship

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


def create_exporter_users(organisation, quantity=1):
    users = []

    for i in range(quantity):
        user = ExporterUser(first_name=faker.first_name(), last_name=faker.last_name(), email=faker.email())
        user.organisation = organisation

        UserOrganisationRelationship(user, organisation).save()
        user.save()

        if quantity == 1:
            return user

        users.append(user)

    return users


def is_not_verified_flag_set_on_good(good):
    flags_on_good = [str(id) for id in good.flags.values_list("id", flat=True)]
    return SystemFlags.GOOD_NOT_YET_VERIFIED_ID in flags_on_good
