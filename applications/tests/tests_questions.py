import unittest

from applications.libraries import questions
from cases.enums import CaseTypeSubTypeEnum
from parameterized import parameterized


class ApplicationQuestionsTest(unittest.TestCase):
    @parameterized.expand(
        [
            (
                CaseTypeSubTypeEnum.F680,
                {},
                {questions.Question.ONE.value: "answer"},
                {questions.Question.ONE.value: "answer"}
            ),
            (
                CaseTypeSubTypeEnum.F680,
                {questions.Question.ONE.value: "answer"},
                {questions.Question.ONE.value: "updated_answer"},
                {questions.Question.ONE.value: "updated_answer"}
            ),
            (
                CaseTypeSubTypeEnum.F680,
                {questions.Question.ONE.value: "answer"},
                {questions.Question.ONE.value: "answer", questions.Question.TWO.value: "answer_2"},
                {questions.Question.ONE.value: "answer", questions.Question.TWO.value: "answer_2"},
            )
        ]
    )
    def test_update_questions(self, application_type, old_questions, new_questions, expected_questions):
        updated_questions = questions.update(
            application_type=application_type,
            old_questions=old_questions,
            new_questions=new_questions
        )

        self.assertEqual(updated_questions, expected_questions)

    def test_invalid_schema_error(self):
        with self.assertRaises(Exception):
            questions.update(
                application_type=CaseTypeSubTypeEnum.F680,
                old_questions={},
                new_questions={"INVALID_QUESTION_FIELD": "answer"}
            )

    def test_invalid_application_type(self):
        with self.assertRaises(Exception):
            questions.update(
                application_type=CaseTypeSubTypeEnum.GOODS,
                old_questions={},
                new_questions={"INVALID_QUESTION_FIELD": "answer"}
            )
