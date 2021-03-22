from django.test import TestCase
from api.letter_templates.helpers import generate_preview


class PreviewTestCase(TestCase):
    def test_generate_preview(self):
        generate_preview(layout="case_context_test", text="Hello World!")
