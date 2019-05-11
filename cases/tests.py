import json

from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from cases.models import Case, CaseNote
from test_helpers.clients import BaseTestClient


class CaseNotesTests(BaseTestClient):

    def setUp(self):
        super().setUp()
        self.draft = self.test_helper.complete_draft('Example Application', self.test_helper.organisation)
        self.application = self.test_helper.submit_draft(self, self.draft)
        self.case = Case.objects.get(application=self.application)
        self.url = reverse('cases:case_notes', kwargs={'pk': self.case.id})

    def test_create_case_note_successful(self):
        data = {
            'text': 'I Am Easy to Find',
        }

        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CaseNote.objects.count(), 1)
        self.assertEqual(CaseNote.objects.get().text, data.get('text'))

    @parameterized.expand([
        '{}',  # Empty data
        '{"text": ""}',  # Empty text field
        '{"text": "🙂"}',  # Less than two character minimum
        '{"text": "' + '🙂' * 2001 + '"}',  # More than two thousand character maximum
    ])
    def test_create_case_note_failure(self, data):
        response = self.client.post(self.url, data=json.loads(data))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CaseNote.objects.count(), 0)
