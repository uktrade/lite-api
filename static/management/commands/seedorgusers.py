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
    pipenv run ./manage.py seedorganisation
    """

    def handle(self, *args, **options):
        _seed_exporter_users(_get_organisation())


def _get_organisation():
    if Organisation.objects.count() > 0:
        return Organisation.objects.all().first()
    else:
        organisation = Organisation(
            name='Test Org',
            eori_number='1234567890AAA',
            sic_number='2345',
            vat_number='GB1234567',
            registration_number='09876543'
        )
        organisation.save()

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

        return organisation


def _seed_exporter_users(organisation: Organisation):
    users = serialize(env('SEED_USERS'))
    print('\n Seeding users...')

    for email in users:
        if ExporterUser.objects.filter(email=email).count() == 0:
            first_name_index = email.find('.')
            first_name = email[0:first_name_index].title()
            last_name_index = email.find('@')
            last_name = email[first_name_index + 1:last_name_index].title()

            exporter_user = ExporterUser(
                email=email,
                first_name=first_name,
                last_name=last_name
            )
            exporter_user.save()

            UserOrganisationRelationship(
                user=exporter_user,
                organisation=organisation,
                status=UserStatuses.ACTIVE
            ).save()

            print('{"email: "' + email + '", "first_name": "' + first_name + '", "last_name": "' + last_name + '"}')
