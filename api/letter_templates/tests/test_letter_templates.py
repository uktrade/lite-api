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
                },
            ]
        }

        with open(
            "api/letter_templates/templates/letter_templates/refusal.html", "r", encoding="utf_8"
        ) as template_file:
            template = Template(template_file.read())

        context = Context({"goods": goods_data})
        rendered_template = template.render(context)

        with open(
            "api/letter_templates/tests/templates/letter_templates/test-refusal.html", "r", encoding="utf_8"
        ) as output_file:
            file_content = output_file.read()

        self.assertEqual(rendered_template, file_content)
