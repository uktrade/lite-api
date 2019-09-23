from django.core.management import BaseCommand
from json import loads as serialize

from addresses.models import Address
from conf.settings import env
from organisations.models import Organisation, Site
from static.countries.helpers import get_country
from users.enums import UserStatuses
from users.models import ExporterUser, UserOrganisationRelationship


class Command(BaseCommand):
    """
    pipenv run ./manage.py seedorgusers
    """

    def handle(self, *args, **options):
        organisation = _get_organisation()
        _seed_exporter_users_to_organisation(organisation)


def _get_organisation():
    print('\nRetrieving organisation...')

    try:
        organisation = Organisation.objects.get(name='Test Org')
    except Organisation.DoesNotExist:
        print('Organisation not found...')
        organisation = _create_organisation()

    print('{"name: "' + organisation.name + '", "id": "' + str(organisation.id) + '"}')
    return organisation


def _create_organisation():
    print('\nCreating organisation...')

    organisation = Organisation(
            name='Test Org',
            eori_number='1234567890AAA',
            sic_number='2345',
            vat_number='GB1234567',
            registration_number='09876543'
    )
    organisation.save()

    _add_site_to_organisation(organisation)
    return organisation


def _add_site_to_organisation(organisation: Organisation):
    address = Address(
        address_line_1='42 Question Road',
        address_line_2='',
        country=get_country('GB'),
        city='London',
        region='London',
        postcode='Islington'
    )
    address.save()

    site = Site(
        name='Headquarters',
        organisation=organisation,
        address=address
    )
    site.save()
    organisation.primary_site = site
    organisation.save()


def _seed_exporter_users_to_organisation(organisation: Organisation):
    print('\nSeeding exporter users...')

    # Do add combine the TEST_EXPORTER_USERS and SEED_USERS env variables in `.env`;
    # this would grant GOV user permissions to the exporter test-user accounts.
    # See `users/migrations/0001_initial.py`
    test_exporter_users = serialize(env('TEST_EXPORTER_USERS'))
    seed_users = serialize(env('SEED_USERS'))
    exporter_users = test_exporter_users + seed_users

    for email in exporter_users:
        exporter_user = _get_exporter_user(email)
        _add_user_to_organisation(exporter_user, organisation)


def _get_exporter_user(exporter_user_email: str):
    try:
        exporter_user = ExporterUser.objects.get(email=exporter_user_email)
    except ExporterUser.DoesNotExist:
        exporter_user = _create_exporter_user(exporter_user_email)
    return exporter_user


def _create_exporter_user(exporter_user_email: str):
    exporter_user = ExporterUser(email=exporter_user_email)
    exporter_user.save()
    return exporter_user


def _add_user_to_organisation(user: ExporterUser, organisation: Organisation):
    if UserOrganisationRelationship.objects.filter(user=user).count() == 0:
        UserOrganisationRelationship(
            user=user,
            organisation=organisation,
            status=UserStatuses.ACTIVE
        ).save()
        print('{"email: "' + user.email + '", "id": "' + str(user.id) + '"}')
