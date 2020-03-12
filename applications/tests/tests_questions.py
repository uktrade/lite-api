import unittest

from applications.libraries.questions import questions
from cases.enums import CaseTypeSubTypeEnum
from parameterized import parameterized


class ApplicationQuestionsTest(unittest.TestCase):
    @parameterized.expand(
        [
            (
                CaseTypeSubTypeEnum.F680,
                {},
                {
                    "foreign_technology": True,
                    "foreign_technology_description": "This is going to Norway."
                },
                {
                    "foreign_technology": True,
                    "foreign_technology_description": "This is going to Norway."
                }
            ),
            (
                CaseTypeSubTypeEnum.F680,
                {"foreign_technology": False},
                {
                    "foreign_technology": True,
                    "foreign_technology_description": "This is going to Norway."
                },
                {
                    "foreign_technology": True,
                    "foreign_technology_description": "This is going to Norway."
                }
            ),
        ]
    )
    def test_update_questions(self, application_type, old_questions, new_questions, expected_questions):
        updated_questions = questions.update(
            application_type=application_type,
            old_questions=old_questions,
            new_questions=new_questions
        )

        self.assertEqual(updated_questions, expected_questions)

    def test_invalid_field_type(self):
        with self.assertRaises(Exception) as e:
            questions.update(
                application_type=CaseTypeSubTypeEnum.GOODS,
                old_questions={},
                new_questions={"foreign_technology": "answer"}
            )
