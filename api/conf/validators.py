from django.utils.deconstruct import deconstructible
from rest_framework.exceptions import ValidationError

from static.control_list_entries.models import ControlListEntry


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
