import random

from flags.enums import SystemFlags
from users.models import ExporterUser, UserOrganisationRelationship


def random_name():
    """
    :return: A randomly generated first name and last name
    """
    first_names = ("John", "Andy", "Joe", "Jane", "Emily", "Kate")
    last_names = ("Johnson", "Smith", "Williams", "Hargreaves", "Montague", "Jenkins")

    first_name = random.choice(first_names)  # nosec
    last_name = random.choice(last_names)  # nosec

    return first_name, last_name


def create_exporter_users(organisation, quantity=1):
    users = []

    for i in range(quantity):
        first_name, last_name = random_name()
        email = f"{first_name}@{last_name}.com"
        if ExporterUser.objects.filter(email=email).count() == 1:
            email = first_name + "." + last_name + str(i) + "@" + organisation.name + ".com"
        user = ExporterUser(first_name=first_name, last_name=last_name, email=email)
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
