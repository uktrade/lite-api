from django.urls import reverse
from rest_framework.test import APITestCase, URLPatternsTestCase, APIClient

from applications.models import Application
from cases.models import Case, CaseNote
from conf.urls import urlpatterns
from drafts.models import Draft
from static.urls import urlpatterns as static_urlpatterns
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

    def create_case_note(self, case: Case, text: str):
        case_note = CaseNote(case=case,
                             text=text)
        case_note.save()
        return case_note

    def submit_draft(self, draft: Draft):
        draft_id = draft.id
        url = reverse('applications:applications')
        data = {'id': draft_id}
        self.client.post(url, data, **self.headers)
        return Application.objects.get(pk=draft_id)
