from django.urls import path, include
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase
from applications.models import Application
from drafts.models import Draft
from test_helpers.org_and_user_helper import OrgAndUserHelper


class DraftTests(APITestCase, URLPatternsTestCase):

    urlpatterns = [
        path('drafts/', include('drafts.urls')),
        path('applications/', include('applications.urls')),
        path('organisations/', include('organisations.urls'))
    ]

    client = APIClient

    def setUp(self):
        self.test_helper = OrgAndUserHelper(name='name')
        self.headers = {'HTTP_USER_ID': str(self.test_helper.user.id)}

    def test_create_draft(self):
        """
            Ensure we can create a new draft object.
        """
        url = reverse('drafts:drafts')
        data = {'name': 'test'}
        response = self.client.post(url, data, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Draft.objects.count(), 1)
        self.assertEqual(Draft.objects.get().name, 'test')

    def test_create_draft_no_user_id(self):
        """
            Ensure we cannot create a draft without a name.
        """
        url = reverse('drafts:drafts')
        response = self.client.post(url, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Application.objects.count(), 0)