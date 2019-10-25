from rest_framework import status
from rest_framework.reverse import reverse

from cases.enums import CaseType
from letter_templates.models import LetterTemplate
from picklists.enums import PickListStatus, PicklistType
from static.letter_layouts.models import LetterLayout
from test_helpers.clients import DataTestClient


class LetterTemplatesListTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.picklist_item = self.create_picklist_item('#1',
                                                       self.team,
                                                       PicklistType.LETTER_PARAGRAPH,
                                                       PickListStatus.ACTIVE)
        self.letter_layout = LetterLayout.objects.first()
        self.letter_template = LetterTemplate.objects.create(name='SIEL',
                                                             restricted_to=",".join([CaseType.CLC_QUERY,
                                                                                     CaseType.END_USER_ADVISORY_QUERY]),
                                                             layout=self.letter_layout)
        self.letter_template.letter_paragraphs.add(self.picklist_item)
        self.url = reverse('letter_templates:letter_templates')

    def test_get_letter_templates(self):
        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()['results'][0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['id'], str(self.letter_template.id))
        self.assertEqual(response_data['name'], self.letter_template.name)
        self.assertEqual(response_data['layout']['id'], self.letter_layout.id)
        self.assertEqual(response_data['letter_paragraphs'], [str(self.picklist_item.id)])
        self.assertIn(CaseType.CLC_QUERY, str(response_data['restricted_to']))
        self.assertIn(CaseType.END_USER_ADVISORY_QUERY, str(response_data['restricted_to']))
        self.assertIn(CaseType.get_text(CaseType.CLC_QUERY), str(response_data['restricted_to_display']))
        self.assertIn(CaseType.get_text(CaseType.END_USER_ADVISORY_QUERY), str(response_data['restricted_to_display']))
        self.assertIsNotNone(response_data.get('created_at'))
        self.assertIsNotNone(response_data.get('last_modified_at'))


class LetterTemplateDetailTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.picklist_item = self.create_picklist_item('#1',
                                                       self.team,
                                                       PicklistType.LETTER_PARAGRAPH,
                                                       PickListStatus.ACTIVE)
        self.letter_layout = LetterLayout.objects.first()
        self.letter_template = LetterTemplate.objects.create(name='SIEL',
                                                             restricted_to=",".join([CaseType.CLC_QUERY,
                                                                                     CaseType.END_USER_ADVISORY_QUERY]),
                                                             layout=self.letter_layout)
        self.letter_template.letter_paragraphs.add(self.picklist_item)
        self.url = reverse('letter_templates:letter_template', kwargs={'pk': self.letter_template.id})

    def test_get_letter_template(self):
        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['id'], str(self.letter_template.id))
        self.assertEqual(response_data['name'], self.letter_template.name)
        self.assertEqual(response_data['layout']['id'], self.letter_layout.id)
        self.assertEqual(response_data['letter_paragraphs'], [str(self.picklist_item.id)])
        self.assertIn(CaseType.CLC_QUERY, response_data['restricted_to'])
        self.assertIn(CaseType.END_USER_ADVISORY_QUERY, response_data['restricted_to'])
        self.assertIn(CaseType.get_text(CaseType.CLC_QUERY), response_data['restricted_to_display'])
        self.assertIn(CaseType.get_text(CaseType.END_USER_ADVISORY_QUERY), response_data['restricted_to_display'])
        self.assertIsNotNone(response_data.get('created_at'))
        self.assertIsNotNone(response_data.get('last_modified_at'))
