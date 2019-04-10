import json
import uuid

from django.urls import path, include
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse, reverse_lazy
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase
from reversion.models import Version

from applications.models import Application
from drafts.models import Draft


class DraftTests(APITestCase, URLPatternsTestCase):

    urlpatterns = [
        path('drafts/', include('drafts.urls')),
        path('applications/', include('applications.urls')),
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
        self.assertEqual(Draft.objects.count(), 1)
        self.assertEqual(Draft.objects.get().user_id, '12345')
        self.assertEqual(Draft.objects.get().name, 'test')

    def test_create_draft_empty_user_id(self):
        """
            Ensure we cannot create a draft with an empty user_id.
        """
        url = reverse('drafts:drafts')
        data = {'user_id': ''}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Draft.objects.count(), 0)

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

        draft = Draft(user_id='12345', name='test')
        draft.save()

        url = reverse('drafts:draft', kwargs={'pk': draft.id})
        data = {'control_code': control_code}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(Draft.objects.count(), 1)
        self.assertEqual(Draft.objects.get().id, draft.id)
        self.assertEqual(Draft.objects.get().control_code, control_code)

    # Viewing

    def test_view_drafts(self):
        """
            Ensure we can get a list of drafts.
        """

        complete_draft = Draft(user_id='12345',
                               control_code='ML2',
                               name='Test',
                               destination='Poland',
                               activity='Trade',
                               usage='Fun')
        complete_draft.save()

        url = '/drafts/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['drafts']), 1)

    def test_view_drafts_not_applications(self):
        """
            Ensure that when a draft is submitted it does not get submitted as an application
        """
        draft_id = '90D6C724-0339-425A-99D2-9D2B8E864EC7'
        complete_draft = Draft(id=draft_id,
                               user_id='12345',
                               control_code='ML2',
                               name='Test',
                               destination='Poland',
                               activity='Trade',
                               usage='Fun')
        complete_draft.save()

        url = '/applications/' + str(draft_id) + '/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_view_draft(self):
        """
            Ensure we can get a draft.
        """
        complete_draft = Draft(user_id='12345',
                               control_code='ML2',
                               name='Test',
                               destination='Poland',
                               activity='Trade',
                               usage='Fun')

        complete_draft.save()

        url = '/drafts/' + str(complete_draft.id) + '/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_view_incorrect_draft(self):
        """
            Ensure we cannot get a draft if the id is incorrect.
        """
        complete_draft = Draft(user_id='12345',
                               control_code='ML2',
                               name='Test',
                               destination='Poland',
                               activity='Trade',
                               usage='Fun')

        complete_draft.save()
        invalid_id = '90D6C724-0339-425A-99D2-9D2B8E864EC6'

        url = '/drafts/' + str(invalid_id) + '/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
