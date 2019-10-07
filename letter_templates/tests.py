from rest_framework import status
from rest_framework.reverse import reverse

from letter_templates.models import LetterTemplate
from picklists.enums import PickListStatus, PicklistType
from static.letter_layouts.models import LetterLayout
from test_helpers.clients import DataTestClient


class LetterTemplatesTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.picklist_item = self.create_picklist_item('#1',
                                                       self.team,
                                                       PicklistType.LETTER_PARAGRAPH,
                                                       PickListStatus.ACTIVE)
        self.letter_layout = LetterLayout.objects.create(id='siel', name='SIEL')
        self.letter_template = LetterTemplate.objects.create(name='SIEL',
                                                             layout=self.letter_layout)
        self.letter_template.letter_paragraphs.add(self.picklist_item)
        self.url = reverse('letter_templates:letter_templates')

    def test_get_letter_templates(self):
        response = self.client.get(self.url)
        response_data = response.json()['results'][0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['id'], str(self.letter_template.id))
        self.assertEqual(response_data['name'], self.letter_template.name)
        self.assertEqual(response_data['layout'], self.letter_layout.id)
        self.assertEqual(response_data['letter_paragraphs'], [str(self.picklist_item.id)])
        self.assertIsNotNone(response_data.get('created_at'))
        self.assertIsNotNone(response_data.get('last_modified_at'))


class LetterTemplateTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.picklist_item = self.create_picklist_item('#1',
                                                       self.team,
                                                       PicklistType.LETTER_PARAGRAPH,
                                                       PickListStatus.ACTIVE)
        self.letter_layout = LetterLayout.objects.create(id='siel', name='SIEL')
        self.letter_template = LetterTemplate.objects.create(name='SIEL',
                                                             layout=self.letter_layout)
        self.letter_template.letter_paragraphs.add(self.picklist_item)
        self.url = reverse('letter_templates:letter_template', kwargs={'pk': self.letter_template.id})

    def test_get_letter_layout(self):
        response = self.client.get(self.url)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['id'], str(self.letter_template.id))
        self.assertEqual(response_data['name'], self.letter_template.name)
        self.assertEqual(response_data['layout'], self.letter_layout.id)
        self.assertEqual(response_data['letter_paragraphs'], [str(self.picklist_item.id)])
        self.assertIsNotNone(response_data.get('created_at'))
        self.assertIsNotNone(response_data.get('last_modified_at'))
