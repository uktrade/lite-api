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

    # Editing

    def test_edit_draft(self):
        """
            Ensure we can edit a draft object.
        """
        draft = Draft(name='test',
                      organisation=self.test_helper.organisation)
        draft.save()

        url = reverse('drafts:draft', kwargs={'pk': draft.id})
        data = {'destination': 'France'}
        response = self.client.put(url, data, format='json', **self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(Draft.objects.count(), 1)
        self.assertEqual(Draft.objects.get().id, draft.id)
        self.assertEqual(Draft.objects.get().destination, 'France')