from django.urls import reverse
from rest_framework import status

from static.control_list_entries.models import ControlListEntry
from test_helpers.clients import DataTestClient


class TriageStageTests(DataTestClient):

    def test_get_triage_stage(self):
        parent_rating = ControlListEntry.create('ML1', 'Parent rating', None)
        child_1 = ControlListEntry.create(rating='ML1a', text='Child 1', parent=parent_rating)
        ControlListEntry.create(rating='ML1b', text='Child 2', parent=parent_rating)
        ControlListEntry.create(rating='ML1b1', text='Child 2-1', parent=child_1)

        url = reverse('static:control_ratings:triage_stage', kwargs={'rating': parent_rating.rating})

        response = self.client.get(url)
        response_data = response.json()['control_rating']

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response_data['rating'], parent_rating.rating)
        self.assertEqual(response_data['text'], parent_rating.text)
        self.assertEqual(len(response_data['children']), 2)

    def test_create_new_rating(self):
        data = {
            'rating': 'ML1a',
            'text': 'This is a child'
        }

        url = reverse('static:control_ratings:control_ratings')
        response = self.client.post(url, data)
        response_data = response.json()['control_rating']

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response_data['rating'], data['rating'])
        self.assertEqual(response_data['text'], data['text'])

        control_rating = ControlListEntry.objects.get()
        self.assertEqual(control_rating.rating, data['rating'])
        self.assertEqual(control_rating.text, data['text'])

    def test_create_new_child_rating(self):
        parent_rating = ControlListEntry.create('ML1', 'Parent rating', None)

        data = {
            'rating': 'ML1a',
            'text': 'This is a child'
        }

        url = reverse('static:control_ratings:triage_stage', kwargs={'rating': parent_rating.rating})

        response = self.client.post(url, data)
        response_data = response.json()['control_rating']

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response_data['rating'], data['rating'])
        self.assertEqual(response_data['text'], data['text'])

        control_rating = ControlListEntry.objects.get(rating=data['rating'])
        self.assertEqual(control_rating.rating, data['rating'])
        self.assertEqual(control_rating.text, data['text'])

    def test_edit_rating(self):
        parent_rating = ControlListEntry.create('ML1', 'Parent rating', None)

        data = {
            'rating': 'ML2',
        }

        url = reverse('static:control_ratings:triage_stage', kwargs={'rating': parent_rating.rating})

        response = self.client.put(url, data)
        response_data = response.json()['control_rating']

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response_data['rating'], data['rating'])

        control_rating = ControlListEntry.objects.get(rating=data['rating'])
        self.assertEqual(control_rating.rating, data['rating'])

    def test_upload(self):
        url = reverse('static:control_ratings:excel_data')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
