import random

from django.urls import path, include
from rest_framework.reverse import reverse
from rest_framework.test import APIClient
from drafts.models import Draft
from goods.models import Good
from organisations.models import Organisation
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
        self.address = "London"
        self.admin_user_first_name = "trinity"
        self.admin_user_last_name = "trinity"
        self.admin_user_email = "trinity@"+name+".com"

        url = reverse('organisations:organisations')
        data = {'name': self.name, 'eori_number': self.eori_number, 'sic_number': self.sic_number,
                'vat_number': self.vat_number, 'registration_number': self.registration_number,
                'address': self.address, 'admin_user_email': self.admin_user_email,
                'admin_user_first_name': self.admin_user_first_name, 'admin_user_last_name': self.admin_user_last_name}
        self.client.post(url, data, format='json')

        self.organisation = Organisation.objects.get(name=name)
        self.user = User.objects.filter(organisation=self.organisation)[0]

    @staticmethod
    def complete_draft(name, org):
        draft = Draft(name=name,
                      destination='Poland',
                      activity='Trade',
                      usage='Fun',
                      organisation=org)
        draft.save()
        return draft

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


def random_name():
    first_names = ('John', 'Andy', 'Joe', 'Jane', 'Emily', 'Kate')
    last_names = ('Johnson', 'Smith', 'Williams', 'Hargreaves', 'Montague', 'Jenkins')

    first_name = random.choice(first_names)
    last_name = random.choice(last_names)

    return first_name, last_name
