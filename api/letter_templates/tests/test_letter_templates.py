from django.test import TestCase
from django.template.loader import render_to_string


class TemplatesTestCase(TestCase):
    def test_refusal_template(self):
        goods_data = {
            "refuse": [
                {
                    "good": {"name": "Test Good 1"},
                    "denial_reasons": [
                        {"display_value": "1", "description": "Test Description 1"},
                        {"display_value": "2", "description": "Test Description 2"},
                    ],
                },
                {
                    "good": {"name": "Test Good 2"},
                    "denial_reasons": [
                        {"display_value": "1", "description": "Test Description 1"},
                        {"display_value": "2", "description": "Test Description 2"},
                    ],
                },
            ]
        }

        rendered_template = render_to_string(
            "letter_templates/refusal.html",
            {"goods": goods_data},
        )

        self.assertIn("Test Good 1", rendered_template)
        self.assertIn("Criterion 1", rendered_template)
        self.assertIn("Test Description 1", rendered_template)
