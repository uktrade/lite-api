import json
import uuid

from django.urls import path, include
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase
from reversion.models import Version

from applications.models import Application


class DraftTests(APITestCase, URLPatternsTestCase):

    urlpatterns = [
        path('drafts/', include('drafts.urls')),
    ]

    client = APIClient()

    # Creation

    def test_create_draft(self):
        """
            Ensure we can create a new draft object.
        """
        url = reverse('drafts:drafts')
        data = {'user_id': 12345, 'name': 'test'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Application.objects.count(), 1)
        self.assertEqual(Application.objects.get().user_id, '12345')
        self.assertEqual(Application.objects.get().name, 'test')

    def test_create_draft_empty_user_id(self):
        """
            Ensure we cannot create a draft with an empty user_id.
        """
        url = reverse('drafts:drafts')
        data = {'user_id': ''}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Application.objects.count(), 0)

    def test_create_draft_no_user_id(self):
        """
            Ensure we cannot create a draft without a user_id.
        """
        url = reverse('drafts:drafts')
        response = self.client.post(url, {'name': 'test'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Application.objects.count(), 0)

    # Editing

    def test_edit_draft(self):
        """
            Ensure we can edit a draft object.
        """
        control_code = 'ML1a'

        draft = Application(user_id='12345', name='test', draft=True)
        draft.save()

        url = reverse('drafts:draft', kwargs={'pk': draft.id})
        data = {'control_code': control_code}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(Application.objects.count(), 1)
        self.assertEqual(Application.objects.get().id, draft.id)
        self.assertEqual(Application.objects.get().control_code, control_code)

    # Viewing

    def test_view_drafts(self):
        """
            Ensure we can get a list of drafts.
            """
        complete_draft = Application(user_id='12345',
                                     control_code='ML2',
                                     name='Test',
                                     destination='Poland',
                                     activity='Trade',
                                     usage='Fun',
                                     draft=True)
        complete_draft.save()

        url = '/drafts/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['drafts']), 1)

    def test_view_drafts_not_applications(self):
        """
            Ensure we can get a list of drafts (and not applications)
            """
        complete_draft = Application(user_id='12345',
                                     control_code='ML2',
                                     name='Test',
                                     destination='Poland',
                                     activity='Trade',
                                     usage='Fun',
                                     draft=False)
        complete_draft.save()

        url = '/drafts/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['drafts']), 0)

    def test_view_draft(self):
        """
            Ensure we can get a draft.
        """
        complete_draft = Application(user_id='12345',
                                     control_code='ML2',
                                     name='Test',
                                     destination='Poland',
                                     activity='Trade',
                                     usage='Fun',
                                     draft=True)
        complete_draft.save()

        url = '/drafts/' + str(complete_draft.id) + '/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_view_draft_not_application(self):
        """
            Ensure we cannot get an application from the drafts endpoint.
        """
        complete_draft = Application(user_id='12345',
                                     control_code='ML2',
                                     name='Test',
                                     destination='Poland',
                                     activity='Trade',
                                     usage='Fun',
                                     draft=False)
        complete_draft.save()

        url = '/drafts/' + str(complete_draft.id) + '/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_view_incorrect_draft(self):
        """
            Ensure we cannot get a draft if the id is incorrect.
        """
        complete_draft = Application(user_id='12345',
                                     control_code='ML2',
                                     name='Test',
                                     destination='Poland',
                                     activity='Trade',
                                     usage='Fun',
                                     draft=True)
        complete_draft.save()

        url = '/drafts/invalid_id/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
