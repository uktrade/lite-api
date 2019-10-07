from rest_framework import status
from rest_framework.reverse import reverse

from letter_templates.models import LetterTemplate
from static.letter_layouts.models import LetterLayout
from test_helpers.clients import DataTestClient


class LetterTemplatesTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.letter_layout = LetterLayout.objects.create(id='siel', name='SIEL')
        self.letter_template = LetterTemplate.objects.create(name='SIEL',
                                                             layout=self.letter_layout,
                                                             content='<p>I Am Easy to Find</p>')
        self.url = reverse('static:letter_layouts:letter_layouts')

    def test_get_letter_layouts(self):
        response = self.client.get(self.url)
        response_data = response.json()['results'][0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(response_data['id'], self.letter_layout.id)
        self.assertIn(response_data['name'], self.letter_layout.name)


class LetterTemplateTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.letter_layout = LetterLayout.objects.create(id='siel', name='SIEL')
        self.url = reverse('static:letter_layouts:letter_layout', kwargs={'pk': self.letter_layout})

    def test_get_letter_layout(self):
        response = self.client.get(self.url)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(response_data['id'], self.letter_layout.id)
        self.assertIn(response_data['name'], self.letter_layout.name)
