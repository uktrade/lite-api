from uuid import UUID

from django.urls import reverse
from rest_framework.test import APITestCase, URLPatternsTestCase, APIClient

from applications.models import Application
from cases.models import CaseNote, Case
from conf.urls import urlpatterns
from drafts.models import Draft
from gov_users.models import GovUser
from organisations.models import Organisation
from queues.models import Queue
from static.urls import urlpatterns as static_urlpatterns
from teams.models import Team
from test_helpers.org_and_user_helper import OrgAndUserHelper


class BaseTestClient(APITestCase, URLPatternsTestCase):
    """
    Base test client which provides only URL patterns and client
    """
    urlpatterns = urlpatterns + static_urlpatterns
    client = APIClient


class DataTestClient(BaseTestClient):
    """
    Test client which creates an initial organisation and user
    """

    def setUp(self):
        super().setUp()
        self.test_helper = OrgAndUserHelper(name='Org1')
        self.headers = {'HTTP_USER_ID': str(self.test_helper.user.id)}
        self.team = Team.objects.get(name='Admin')
        self.user = GovUser(id=UUID('43a88949-5db9-4334-b0cc-044e91827451'),
                            email='test@mail.com',
                            first_name='John',
                            last_name='Smith',
                            team=self.team)
        self.user.save()
        self.gov_headers = {'HTTP_GOV_USER_TOKEN': str(self.user.id)}

    def create_organisation(self, name):
        self.name = name
        self.eori_number = "GB123456789000"
        self.sic_number = "2765"
        self.vat_number = "123456789"
        self.registration_number = "987654321"

        # Site name
        self.site_name = "headquarters"

        # Address details
        self.country = 'GB'
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
        self.client.post(url, data, **self.headers)

    def create_case_note(self, case: Case, text: str):
        case_note = CaseNote(case=case,
                             text=text,
                             user=self.user)
        case_note.save()
        return case_note

    def create_queue(self, name: str, team: Team):
        queue = Queue(name=name,
                      team=team)
        queue.save()
        return queue

    def create_gov_user(self, email: str, team: Team):
        gov_user = GovUser(email=email,
                           team=team)
        gov_user.save()
        return gov_user

    def create_team(self, name: str):
        team = Team(name=name)
        team.save()
        return team

    def submit_draft(self, draft: Draft):
        draft_id = draft.id
        url = reverse('applications:applications')
        data = {'id': draft_id}
        self.client.post(url, data, **self.headers)
        return Application.objects.get(pk=draft_id)
