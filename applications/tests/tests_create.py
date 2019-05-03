from django.urls import path, include, reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase

from applications.models import Application
from cases.models import Case
from queues.models import Queue
from test_helpers.org_and_user_helper import OrgAndUserHelper


class ApplicationsTests(APITestCase, URLPatternsTestCase):

    urlpatterns = [
        path('drafts/', include('drafts.urls')),
        path('applications/', include('applications.urls')),
        path('organisations/', include('organisations.urls'))
    ]

    client = APIClient()

    def setUp(self):
        self.test_helper = OrgAndUserHelper(name='name')
        self.headers = {'HTTP_USER_ID': str(self.test_helper.user.id)}

    def test_create_application_case_and_addition_to_queue(self):
        """
            Test whether we can create a draft first and then submit it as an application
        """

        draft = OrgAndUserHelper.complete_draft(name='test', org=self.test_helper.organisation)
        draft_id = draft.id
        self.assertEqual(Queue.objects.get(pk='00000000-0000-0000-0000-000000000001').cases.count(), 0)
        url = reverse('applications:applications')
        data = {'id': draft_id}
        response = self.client.post(url, data, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Application.objects.get(pk=draft_id).status.name, "submitted")
        self.assertEqual(Case.objects.get(application=Application.objects.get(pk=draft_id)).application,
                         Application.objects.get(pk=draft_id))
        self.assertEqual(Queue.objects.get(pk='00000000-0000-0000-0000-000000000001').cases.count(), 1)

    def test_create_application_with_invalid_id(self):
        """
            Ensure we cannot create a new application object with an invalid draft id.
        """
        draft_id = '90D6C724-0339-425A-99D2-9D2B8E864EC7'

        OrgAndUserHelper.complete_draft(name='test', org=self.test_helper.organisation)

        url = reverse('applications:applications')
        data = {'id': draft_id}
        response = self.client.post(url, data, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
