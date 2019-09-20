from rest_framework.exceptions import ErrorDetail

from content_strings.strings import get_string


def check_refusal_errors(advice):
    if advice['type'].lower() == 'refuse' and not advice['text']:
        return {'errors': [{'text': [ErrorDetail(string=get_string('cases.advice_refusal_error'), code='blank')]}]}
    return None
