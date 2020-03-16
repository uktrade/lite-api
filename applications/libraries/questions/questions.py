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
    print('\n')
    print('old questions')
    print(old_questions)
    print('new questions')
    print(new_questions)
    print('\n')

    questions = deepcopy(old_questions)
    questions.update(new_questions)

    from pprint import pprint
    pprint(questions)
    serializer = SERIALIZERS[application_type](data=questions, partial=True)

    if not serializer.is_valid():
        print("HERE IS ERRRO")
        print(serializer.errors)
        raise QuestionsError("Invalid questions", errors=serializer.errors)

    # questions.update(serializer.validated_data)

    return serializer.validated_data


def serialize(application_type: CaseTypeSubTypeEnum, questions: Dict):
    print('SERIALIZING~')
    print(questions)
    serializer = SERIALIZERS[application_type](data=questions, partial=True)
    if not serializer.is_valid():
        raise QuestionsError("Invalid questions", errors=serializer.errors)
    print(serializer.data)
    return serializer.data
