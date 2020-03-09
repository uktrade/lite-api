from copy import deepcopy
from typing import Dict

import enum

from cases.enums import CaseTypeSubTypeEnum


class QuestionsError(Exception):
    def __init__(self, message, errors):
        super(QuestionsError, self).__init__(message)
        self.errors = errors


class Question(enum.Enum):
    ONE = "What is your question 1?"
    TWO = "What is your question 2?"
    THREE = "What is your question 3?"
    FOUR = "What is your question 4?"


SCHEMA = {
    CaseTypeSubTypeEnum.F680: {
        Question.ONE.value,
        Question.TWO.value,
        Question.THREE.value,
        Question.FOUR.value,
    }
}


def validate(application_type: CaseTypeSubTypeEnum, questions: Dict):
    """
    Checks new questions match the schema for a given application type.
    """
    schema = SCHEMA[application_type]

    return set(questions).issubset(schema)


def update(application_type: CaseTypeSubTypeEnum, old_questions: Dict, new_questions: Dict):
    """
    Update and validates a question set for a given application type.
    """
    questions = deepcopy(old_questions)

    if not validate(application_type, new_questions):
        raise QuestionsError("Invalid questions", errors=new_questions)

    questions.update(new_questions)

    return questions
