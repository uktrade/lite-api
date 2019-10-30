from io import StringIO
from django.core.management import call_command

from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse

from static.letter_layouts.models import LetterLayout
from static.management.commands.seedlayouts import success_message, layouts
from test_helpers.clients import DataTestClient


class LetterLayoutsTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.letter_layout = LetterLayout.objects.first()
        self.url = reverse('static:letter_layouts:letter_layouts')

    def test_get_letter_layouts_success(self):
        response = self.client.get(self.url)
        response_data = response.json()['results'][0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['id'], self.letter_layout.id)
        self.assertEqual(response_data['name'], self.letter_layout.name)


class LetterLayoutTests(DataTestClient):

    def setUp(self):
        super().setUp()
        self.letter_layout = LetterLayout.objects.first()
        self.url = reverse('static:letter_layouts:letter_layout', kwargs={'pk': self.letter_layout.id})

    def test_get_letter_layout_success(self):
        response = self.client.get(self.url)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['id'], self.letter_layout.id)
        self.assertEqual(response_data['name'], self.letter_layout.name)


class SeedTemplatesTests(TestCase):

    def test_seed_layout_command_output(self):
        out = StringIO()
        call_command('seedlayouts', stdout=out)

        self.assertIn(success_message, out.getvalue())
        self.assertTrue(LetterLayout.objects.count() == len(layouts))
