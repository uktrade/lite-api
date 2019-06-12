from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from cases.models import Case, CaseNote
from test_helpers.clients import DataTestClient


class CaseNotesCreateTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.draft = self.test_helper.create_draft_with_good_end_user_and_site('Example Application', self.test_helper.organisation)
        self.application = self.test_helper.submit_draft(self, self.draft)
        self.case = Case.objects.get(application=self.application)
        self.url = reverse('cases:case_notes', kwargs={'pk': self.case.id})

    def test_create_case_note_successful(self):
        data = {
            'text': 'I Am Easy to Find',
        }

        response = self.client.post(self.url, data=data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CaseNote.objects.count(), 1)
        self.assertEqual(CaseNote.objects.get().text, data.get('text'))

    @parameterized.expand([
        [{}],  # Empty data
        [{'text': ''}],  # Empty text field
        [{'text': '🙂'}],  # Less than two character minimum
        [{'text': '🙂' * 2201}],  # More than two thousand, two hundred character maximum
    ])
    def test_create_case_note_failure(self, data):
        response = self.client.post(self.url, data=data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CaseNote.objects.count(), 0)


class CaseNotesViewTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.draft = self.test_helper.create_draft_with_good_end_user_and_site('Example Application', self.test_helper.organisation)
        self.draft2 = self.test_helper.create_draft_with_good_end_user_and_site('Example Application 2', self.test_helper.organisation)
        self.application = self.test_helper.submit_draft(self, self.draft)
        self.application2 = self.test_helper.submit_draft(self, self.draft2)
        self.case = Case.objects.get(application=self.application)
        self.case2 = Case.objects.get(application=self.application2)
        self.url = reverse('cases:case_notes', kwargs={'pk': self.case.id})

    def test_create_case_note_successful(self):
        CaseNote(text='Hairpin Turns',
                 case=self.case).save()
        CaseNote(text='Not in Kansas',
                 case=self.case).save()
        CaseNote(text='Dust Swirls In Strange Light',
                 case=self.case).save()
        CaseNote(text='Rylan',
                 case=self.case2).save()

        response = self.client.get(self.url, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json().get('case_notes')), 3)
