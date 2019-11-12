from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from static.control_list_entries.models import ControlListEntry
from test_helpers.clients import DataTestClient


class TriageStageTests(DataTestClient):

    def test_get_triage_stage(self):
        parent_rating = ControlListEntry.create('ML1b', 'Parent rating', None, False)
        child_1 = ControlListEntry.create(rating='ML1c', text='Child 1', parent=parent_rating, is_decontrolled=False)
        ControlListEntry.create(rating='ML1d', text='Child 2', parent=parent_rating, is_decontrolled=False)
        ControlListEntry.create(rating='ML1d1', text='Child 2-1', parent=child_1, is_decontrolled=False)

        url = reverse('static:control_list_entries:control_list_entry', kwargs={'rating': parent_rating.rating})

        response = self.client.get(url)
        response_data = response.json()['control_list_entry']

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response_data['rating'], parent_rating.rating)
        self.assertEqual(response_data['text'], parent_rating.text)
        self.assertEqual(len(response_data['children']), 2)


class SeedControlListEntriesTests(TestCase):

    def test_seed_control_list_entries_command_output(self):
        out = StringIO()
        call_command('seedcontrollistentries', stdout=out)

        self.assertIn('Control List Entries updated successfully!', out.getvalue())
        self.assertTrue(ControlListEntry.objects.count() > 3000)
