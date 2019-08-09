from uuid import UUID

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework.test import APITestCase, URLPatternsTestCase, APIClient

from applications.models import Application
from cases.enums import CaseType
from cases.models import CaseNote, Case, CaseDocument
from conf.urls import urlpatterns
from drafts.models import Draft
from flags.models import Flag
from goodstype.models import GoodsType
from gov_users.libraries.user_to_token import user_to_token
from picklists.models import PicklistItem
from queues.models import Queue
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_from_status
from static.urls import urlpatterns as static_urlpatterns
from teams.models import Team
from test_helpers.org_and_user_helper import OrgAndUserHelper
from users.models import GovUser, BaseUser


class BaseTestClient(APITestCase, URLPatternsTestCase):
    """
    Base test client which provides only URL patterns and client
    """
    urlpatterns = urlpatterns + static_urlpatterns
    client = APIClient

    def get(self, path, data=None, follow=False, **extra):
        response = self.client.get(path, data, follow, **extra)
        return response.json(), response.status_code


class DataTestClient(BaseTestClient):
    """
    Test client which creates an initial organisation and user
    """

    def setUp(self):
        super().setUp()
        self.test_helper = OrgAndUserHelper(name='Org1')
        self.exporter_headers = {'HTTP_EXPORTER_USER_TOKEN': user_to_token(self.test_helper.user)}
        self.team = Team.objects.get(name='Admin')

        self.exporter_user = self.test_helper.user

        self.gov_user = GovUser(id=UUID('43a88949-5db9-4334-b0cc-044e91827451'),
                                email='test@mail.com',
                                first_name='John',
                                last_name='Smith',
                                team=self.team)
        self.gov_user.save()
        self.queue = Queue.objects.get(team=self.team)
        self.gov_headers = {'HTTP_GOV_USER_TOKEN': user_to_token(self.gov_user)}

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
        self.client.post(url, data, **self.exporter_headers)

    def create_application_case(self, name):
        return Case.objects.get(
            application=self.test_helper.submit_draft(
                self, self.test_helper.create_draft_with_good_end_user_and_site(
                    name,
                    self.test_helper.organisation)))

    def create_clc_query_case(self, name, status=None):
        if not status:
            status = get_case_status_from_status(CaseStatusEnum.SUBMITTED)
        clc_query = self.test_helper.create_clc_query(name, self.test_helper.organisation, status)
        case = Case(clc_query=clc_query, type=CaseType.CLC_QUERY)
        case.save()
        return case

    def create_case_note(self, case: Case, text: str, user: BaseUser, is_visible_to_exporter: bool = False):
        case_note = CaseNote(case=case,
                             text=text,
                             user=user,
                             is_visible_to_exporter=is_visible_to_exporter)
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
        self.client.post(url, data, **self.exporter_headers)
        return Application.objects.get(pk=draft_id)

    def create_case_document(self, case: Case, user: GovUser, name: str):
        case_doc = CaseDocument(case=case,
                                description='This is a document',
                                user=user,
                                name=name,
                                s3_key='thisisakey',
                                size=123456,
                                virus_scanned_at=None,
                                safe=None)
        case_doc.save()
        return case_doc

    def create_flag(self, name: str, level: str, team: Team):
        flag = Flag(name=name, level=level, team=team)
        flag.save()
        return flag

    def create_goods_type(self, content_type_model, obj):
        goodstype = GoodsType(description='thing',
                              is_good_controlled=False,
                              control_code='ML1a',
                              is_good_end_product=True,
                              content_type=ContentType.objects.get(model=content_type_model),
                              object_id=obj.pk,
                              )
        goodstype.save()
        return goodstype

    def create_picklist_item(self, name, team: Team, picklist_type, status):
        picklist_item = PicklistItem(team=team,
                                     name=name,
                                     text='This is a string of text, please do not disturb the milk argument',
                                     type=picklist_type,
                                     status=status)

        picklist_item.save()
        return picklist_item
