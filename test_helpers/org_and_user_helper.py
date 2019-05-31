import random

from django.urls import path, include
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from addresses.models import Address
from applications.enums import ApplicationLicenceType, ApplicationExportType
from applications.models import Application
from drafts.models import Draft, GoodOnDraft, SiteOnDraft
from end_user.enums import EndUserType
from end_user.models import EndUser
from goods.models import Good
from organisations.models import Organisation, Site, ExternalSite
from static.units.units import Units
from users.models import User


class OrgAndUserHelper:
    urlpatterns = [
        path('drafts/', include('drafts.urls')),
        path('applications/', include('applications.urls')),
        path('organisations/', include('organisations.urls'))
    ]

    client = APIClient()

    def __init__(self, name):
        self.name = name
        self.eori_number = "GB123456789000"
        self.sic_number = "2765"
        self.vat_number = "123456789"
        self.registration_number = "987654321"

        # Site name
        self.site_name = "headquarters"

        # Address details
        self.country = "England"
        self.address_line_1 = "42 Industrial Estate"
        self.address_line_2 = "Queens Road"
        self.region = "Hertfordshire"
        self.postcode = "AL1 4GT"
        self.city = "St Albans"

        # First admin user details
        self.admin_user_first_name = "Trinity"
        self.admin_user_last_name = "Fishburne"
        self.admin_user_email = "trinity@" + name + ".com"
        self.password = "password123"

        url = reverse('organisations:organisations')
        data = {
            'name': self.name,
            'eori_number': self.eori_number,
            'sic_number': self.sic_number,
            'vat_number': self.vat_number,
            'registration_number': self.registration_number,
            # Site details
            'site': {
                'name': self.site_name,
                # Address details
                'address': {
                    'country': self.country,
                    'address_line_1': self.address_line_1,
                    'address_line_2': self.address_line_2,

                    'region': self.region,
                    'postcode': self.postcode,
                    'city': self.city,
                },
            },
            # First admin user details
            'user': {
                'first_name': self.admin_user_first_name,
                'last_name': self.admin_user_last_name,
                'email': self.admin_user_email,
                'password': self.password
            },
        }
        self.client.post(url, data, format='json')

        self.organisation = Organisation.objects.get(name=name)
        self.user = User.objects.filter(organisation=self.organisation)[0]
        self.primary_site = self.organisation.primary_site
        self.address = self.primary_site.address

    @staticmethod
    def complete_draft(name, org):
        draft = Draft(name=name,
                      licence_type=ApplicationLicenceType.STANDARD_LICENCE,
                      export_type=ApplicationExportType.PERMANENT,
                      reference_number_on_information_form='',
                      activity='Trade',
                      usage='Fun',
                      organisation=org)
        draft.save()
        return draft

    @staticmethod
    def create_draft_with_good_end_user_and_site(name, org):
        draft = OrgAndUserHelper.complete_draft(name, org)
        good = OrgAndUserHelper.create_controlled_good('a thing', org)
        good.save()
        GoodOnDraft(good=good, draft=draft, quantity=10, unit=Units.NAR, value=500).save()
        draft.end_user = OrgAndUserHelper.create_end_user('test', org)
        SiteOnDraft(site=org.primary_site, draft=draft).save()
        draft.save()
        return draft

    @staticmethod
    def submit_draft(self, draft):
        draft_id = draft.id
        url = reverse('applications:applications')
        data = {'id': draft_id}
        self.client.post(url, data, format='json', **self.headers)
        return Application.objects.get(pk=draft_id)

    @staticmethod
    def create_controlled_good(description, org):
        good = Good(description=description,
                    is_good_controlled=True,
                    control_code='ML1',
                    is_good_end_product=True,
                    part_number='123456',
                    organisation=org)
        good.save()
        return good

    @staticmethod
    def create_additional_users(org, quantity=1):
        users = []
        for i in range(quantity):
            first_name, last_name = random_name()
            email = first_name+'.'+last_name+'@'+org.name+'.com'
            if User.objects.filter(email=email).count() == 1:
                email = first_name+'.'+last_name+str(i)+'@'+org.name+'.com'
            user = User(first_name=first_name,
                        last_name=last_name,
                        email=email,
                        organisation=org)
            user.set_password('password')
            user.save()
            if quantity == 1:
                return user

            users.append(user)

        return users

    @staticmethod
    def create_site(name, org):
        address = Address(address_line_1='42 Road',
                          address_line_2='',
                          country='England',
                          city='London',
                          region='Buckinghamshire',
                          postcode='E14QW')
        address.save()
        site = Site(name=name,
                    organisation=org,
                    address=address)
        site.save()
        return site, address

    @staticmethod
    def create_external_site(name, org):
        external_site = ExternalSite(name=name,
                                     address='20 Questions Road, Enigma',
                                     country='Canada',
                                     organisation=org)
        external_site.save()
        return external_site

    @staticmethod
    def create_end_user(name, organisation):
        end_user = EndUser(name=name,
                           organisation=organisation,
                           address='42 Road, London, Buckinghamshire',
                           website='www.'+name+'.com',
                           type=EndUserType.GOVERNMENT,
                           country='England')
        end_user.save()
        return end_user


def random_name():
    first_names = ('John', 'Andy', 'Joe', 'Jane', 'Emily', 'Kate')
    last_names = ('Johnson', 'Smith', 'Williams', 'Hargreaves', 'Montague', 'Jenkins')

    first_name = random.choice(first_names)
    last_name = random.choice(last_names)

    return first_name, last_name
