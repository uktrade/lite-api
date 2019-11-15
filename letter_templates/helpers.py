from conf.exceptions import NotFoundError
from letter_templates.models import LetterTemplate


def get_letter_template(pk):
    try:
        return LetterTemplate.objects.get(pk=pk)
    except LetterTemplate.DoesNotExist:
        raise NotFoundError(
            {"letter_template": "LetterTemplate not found - " + str(pk)}
        )
