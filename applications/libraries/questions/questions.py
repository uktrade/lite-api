from copy import deepcopy
from typing import Dict

from applications.libraries.questions.serializers import F680JsonSerializer
from cases.enums import CaseTypeSubTypeEnum


class QuestionsError(Exception):
    def __init__(self, message, errors):
        super(QuestionsError, self).__init__(message)
        self.errors = errors


SERIALIZERS = {CaseTypeSubTypeEnum.F680: F680JsonSerializer}


def update(application_type: CaseTypeSubTypeEnum, old_questions: Dict, new_questions: Dict):
    """
    Update and validates a question set for a given application type.
    """
    questions = deepcopy(old_questions)
    old_fields = set(old_questions.keys())
    new_fields = set(new_questions.keys())
    removed_fields = old_fields - new_fields

    for removed_field in removed_fields:
        del questions[removed_field]

    questions.update(new_questions)

    serializer = SERIALIZERS[application_type](data=questions, partial=True)

    if not serializer.is_valid():
        raise QuestionsError("Invalid questions", errors=serializer.errors)

    return serializer.validated_data


def serialize(application_type: CaseTypeSubTypeEnum, questions: Dict):
    serializer = SERIALIZERS[application_type](data=questions, partial=True)
    if not serializer.is_valid():
        raise QuestionsError("Invalid questions", errors=serializer.errors)
    return serializer.to_representation(serializer.validated_data)
