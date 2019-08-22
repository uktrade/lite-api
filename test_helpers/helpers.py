import random

from users.models import ExporterUser, UserOrganisationRelationship


def random_name():
    """
    :return: A randomly generated first name and last name
    """
    first_names = ('John', 'Andy', 'Joe', 'Jane', 'Emily', 'Kate')
    last_names = ('Johnson', 'Smith', 'Williams', 'Hargreaves', 'Montague', 'Jenkins')

    first_name = random.choice(first_names)
    last_name = random.choice(last_names)

    return first_name, last_name


def create_exporter_users(organisation, quantity=1):
    users = []

    for i in range(quantity):
        first_name, last_name = random_name()
        email = f'{first_name}@{last_name}.com'
        if ExporterUser.objects.filter(email=email).count() == 1:
            email = first_name + '.' + last_name + str(i) + '@' + organisation.name + '.com'
        user = ExporterUser(first_name=first_name,
                            last_name=last_name,
                            email=email)
        user.organisation = organisation

        UserOrganisationRelationship(user, organisation).save()
        user.save()

        if quantity == 1:
            return user

        users.append(user)

    return users
