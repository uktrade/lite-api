from django.test import tag
from rest_framework import status
from rest_framework.reverse import reverse

from letter_templates.models import LetterTemplate
from picklists.enums import PickListStatus, PicklistType
from static.letter_layouts.models import LetterLayout
from test_helpers.clients import DataTestClient


class LetterTemplateCreateTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.picklist_item_1 = self.create_picklist_item('#1',
                                                         self.team,
                                                         PicklistType.LETTER_PARAGRAPH,
                                                         PickListStatus.ACTIVE)
        self.picklist_item_2 = self.create_picklist_item('#2',
                                                         self.team,
                                                         PicklistType.LETTER_PARAGRAPH,
                                                         PickListStatus.ACTIVE)
        self.letter_layout = LetterLayout.objects.create(id='siel', name='SIEL')
        self.url = reverse('letter_templates:letter_templates')

    def test_create_letter_templates(self):
        """
        Successfully create a letter template
        """
        data = {
            'name': 'Letter Template',
            'layout': self.letter_layout.id,
            'letter_paragraphs': [
                self.picklist_item_1.id,
                self.picklist_item_2.id
            ]
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        letter_template = LetterTemplate.objects.get()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(letter_template.name, data['name'])
        self.assertEqual(letter_template.layout.id, data['layout'])
        self.assertEqual(list(letter_template.letter_paragraphs.values_list('id', flat=True)),
                         data['letter_paragraphs'])

    @tag('only')
    def test_create_letter_templates_not_unique_name_failure(self):
        """
        Fail as the name is not unique
        """
        self.letter_template = LetterTemplate.objects.create(name='SIEL', layout=self.letter_layout)
        self.letter_template.letter_paragraphs.add(self.picklist_item_1)

        data = {
            'name': 'Letter Template',
            'layout': self.letter_layout.id,
            'letter_paragraphs': [
                self.picklist_item_1.id,
                self.picklist_item_2.id
            ]
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_letter_templates_no_letter_paragraphs_failure(self):
        """
        Fail as there are no letter paragraphs provided
        """
        data = {
            'name': 'Letter Template',
            'layout': self.letter_layout.id,
            'letter_paragraphs': []
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_letter_templates_no_layout_failure(self):
        """
        Fail as a layout has not been provided
        """
        data = {
            'name': 'Letter Template',
            'letter_paragraphs': [
                self.picklist_item_1.id,
                self.picklist_item_2.id
            ]
        }

        response = self.client.post(self.url, data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
