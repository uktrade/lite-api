from django.test import TestCase
from django.template import Template, Context


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

        with open(
            "api/letter_templates/templates/letter_templates/refusal.html", "r", encoding="utf_8"
        ) as template_file:
            template = Template(template_file.read())

        context = Context({"goods": goods_data})
        rendered_template = template.render(context)

        self.assertIn("Test Good 1", rendered_template)
        self.assertIn("Criterion 1", rendered_template)
        self.assertIn("Test Description 1", rendered_template)
