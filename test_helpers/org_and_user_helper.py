import json

from django.urls import path, include
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase
from applications.models import Application
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
        self.admin_user_email = "trinity@"+name+".com"

        url = reverse('organisations:organisations')
        data = {'name': self.name, 'eori_number': self.eori_number, 'sic_number': self.sic_number,
                'vat_number': self.vat_number, 'registration_number': self.registration_number,
                'address': self.address, 'admin_user_email': self.admin_user_email}
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