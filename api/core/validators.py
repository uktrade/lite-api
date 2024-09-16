from django.utils.deconstruct import deconstructible
from rest_framework.exceptions import ValidationError
import re
from api.staticdata.control_list_entries.models import ControlListEntry


@deconstructible
class ControlListEntryValidator:
    """Validate that the string doesn't contain the null character."""

    message = "Enter a valid control list entry"
    code = "invalid_control_list_entry"

    def __init__(self, message=None, code=None):
        if message is not None:
            self.message = message
        if code is not None:
            self.code = code

    def __call__(self, value):
        try:
            ControlListEntry.objects.get(rating=value)
        except ControlListEntry.DoesNotExist:
            raise ValidationError(self.message, code=self.code)


class EdifactStringValidator:
    message = "Undefined Error"
    regex_string = r"^[a-zA-Z0-9 .,\-\)\(\/'+:=\?\!\"%&\*;\<\>]+$"

    def __call__(self, value):
        match_regex = re.compile(self.regex_string)
        is_value_valid = bool(match_regex.match(value))
        if not is_value_valid:
            raise ValidationError(self.message)


class GoodNameValidator(EdifactStringValidator):
    message = "Product name must only include letters, numbers, and common special characters such as hyphens, brackets and apostrophes"


class PartyAddressValidator(EdifactStringValidator):
    regex_string = re.compile(r"^[a-zA-Z0-9 .,\-\)\(\/'+:=\?\!\"%&\*;\<\>\r\n]+$")
    message = "Address must only include letters, numbers, and common special characters such as hyphens, brackets and apostrophes"
