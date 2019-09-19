from subprocess import call as execute_bash_command
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
        _execute_bash_command(['pipenv', 'run', './manage.py', 'makemigrations'])
        _execute_bash_command(['pipenv', 'run', './manage.py', 'migrate'])
        _seed_exporter_users(_get_organisation())


def _execute_bash_command(command: []):
    print('\n`' + (' '.join(command)) + '`\n')
    execute_bash_command(command)


def _get_organisation():
    if Organisation.objects.count() == 0:
        organisation = Organisation(
            name='Lemonworld Co',
            eori_number='123',
            sic_number='123',
            vat_number='123',
            registration_number='123'
        )
        organisation.save()

        address = Address(
            address_line_1='42 Road',
            address_line_2='',
            country=get_country('GB'),
            city='London',
            region='Buckinghamshire',
            postcode='E14QW'
        )
        address.save()

        site = Site(
            name='Lemonworld HQ',
            organisation=organisation,
            address=address
        )
        site.save()

        organisation.primary_site = site
        organisation.save()

        return organisation
    else:
        return Organisation.objects.all().first()


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
