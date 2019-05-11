from django.urls import reverse
from rest_framework import status

from cases.models import Case, CaseNote
from test_helpers.clients import BaseTestClient


class CaseNotesTests(BaseTestClient):

    def setUp(self):
        super().setUp()
        self.draft = self.test_helper.complete_draft('Example Application', self.test_helper.organisation)
        self.application = self.test_helper.submit_draft(self, self.draft)
        self.case = Case.objects.get(application=self.application)

    def test_create_case_note(self):
        data = {
            'text': 'I Am Easy to Find',
        }

        response = self.client.post(reverse('cases:case_notes', kwargs={'pk': self.case.id}), data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CaseNote.objects.count(), 1)
        self.assertEqual(CaseNote.objects.get().text, data.get('text'))

    def test_cannot_create_empty_case_note(self):
        data = {}

        response = self.client.post(reverse('cases:case_notes', kwargs={'pk': self.case.id}), data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CaseNote.objects.count(), 0)

    def test_cannot_create_case_note_less_than_2_characters(self):
        data = {
            'text': '🙂'
        }

        response = self.client.post(reverse('cases:case_notes', kwargs={'pk': self.case.id}), data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CaseNote.objects.count(), 0)

    def test_cannot_create_case_note_more_than_2000_characters(self):
        data = {
            'text': '🙂' * 2001,
        }

        response = self.client.post(reverse('cases:case_notes', kwargs={'pk': self.case.id}), data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CaseNote.objects.count(), 0)

