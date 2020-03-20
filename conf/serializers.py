import six
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.fields import (
    Field,
    iter_options,
    to_choices_dict,
    flatten_choices_dict,
    CharField,
    empty,
    SkipField,
)
from rest_framework.relations import PrimaryKeyRelatedField

from conf.validators import ControlListEntryValidator
from lite_content.lite_api import strings
from static.countries.models import Country
from static.countries.serializers import CountrySerializer


class PrimaryKeyRelatedSerializerField(PrimaryKeyRelatedField):
    def __init__(self, **kwargs):
        self.serializer = kwargs.pop("serializer", None)

        if not self.serializer:
            raise Exception("PrimaryKeyRelatedSerializerField must define a 'serializer' attribute.")

        super(PrimaryKeyRelatedSerializerField, self).__init__(**kwargs)

    def use_pk_only_optimization(self):
        return False

    def to_representation(self, value):
        return self.serializer(value).data


class CountrySerializerField(PrimaryKeyRelatedSerializerField):
    def __init__(self, **kwargs):
        self.queryset = Country.objects.all()
        self.error_messages = {"null": strings.Addresses.NULL_COUNTRY}
        super().__init__(serializer=CountrySerializer, **kwargs)

    def validate_empty_values(self, data):
        """
        Validate empty values, and either:

        * Raise `ValidationError`, indicating invalid data.
        * Raise `SkipField`, indicating that the field should be ignored.
        * Return (True, data), indicating an empty value that should be
          returned without any further validation being applied.
        * Return (False, data), indicating a non-empty value, that should
          have validation applied as normal.
        """
        if self.read_only:
            return (True, self.get_default())

        if data is empty:
            if getattr(self.root, "partial", False):
                raise SkipField()
            if self.required:
                self.fail("required")
            return (True, self.get_default())

        if data is None:
            if not self.allow_null:
                raise serializers.ValidationError(strings.Addresses.NULL_COUNTRY)
            # Nullable `source='*'` fields should not be skipped when its named
            # field is given a null value. This is because `source='*'` means
            # the field is passed the entire object, which is not null.
            elif self.source == "*":
                return (False, None)
            return (True, None)

        return (False, data)

    def to_internal_value(self, data):
        if self.pk_field is not None:
            data = self.pk_field.to_internal_value(data)
        try:
            return self.get_queryset().get(pk=data)
        except ObjectDoesNotExist:
            raise serializers.ValidationError(strings.Addresses.NULL_COUNTRY)
        except (TypeError, ValueError):
            self.fail("incorrect_type", data_type=type(data).__name__)


class KeyValueChoiceField(Field):
    default_error_messages = {"invalid_choice": _('"{input}" is not a valid choice.')}
    html_cutoff = None
    html_cutoff_text = _("More than {count} items...")

    def __init__(self, choices, **kwargs):
        self.choices = choices
        self.html_cutoff = kwargs.pop("html_cutoff", self.html_cutoff)
        self.html_cutoff_text = kwargs.pop("html_cutoff_text", self.html_cutoff_text)

        self.allow_blank = kwargs.pop("allow_blank", False)

        super(KeyValueChoiceField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        if data == "" and self.allow_blank:
            return ""

        try:
            return self.choice_strings_to_values[six.text_type(data)]
        except KeyError:
            self.fail("invalid_choice", input=data)

    def to_representation(self, value):
        if value in ("", None):
            return value
        return {"key": six.text_type(value), "value": self.choices[value]}

    def iter_options(self):
        """
        Helper method for use with templates rendering select widgets.
        """
        return iter_options(self.grouped_choices, cutoff=self.html_cutoff, cutoff_text=self.html_cutoff_text,)

    def _get_choices(self):
        return self._choices

    def _set_choices(self, choices):
        self.grouped_choices = to_choices_dict(choices)
        self._choices = flatten_choices_dict(self.grouped_choices)

        # Map the string representation of choices to the underlying value.
        # Allows us to deal with eg. integer choices while supporting either
        # integer or string input, but still get the correct datatype out.
        self.choice_strings_to_values = {six.text_type(key): key for key in self.choices}

    choices = property(_get_choices, _set_choices)


class ControlListEntryField(CharField):
    default_error_messages = {
        "blank": _("Enter a valid control list entry"),
        "invalid": _("Enter a valid control list entry"),
    }

    def __init__(self, **kwargs):
        super(ControlListEntryField, self).__init__(**kwargs)
        self.validators.append(ControlListEntryValidator())
