import re

import six
from compat import JsonResponse
from django.http import Http404
from django.utils.translation import ugettext_lazy as _
from rest_framework import status
from rest_framework.fields import Field, iter_options, to_choices_dict, flatten_choices_dict
from rest_framework.relations import PrimaryKeyRelatedField

from organisations.libraries.get_organisation import get_organisation_by_user


class PrimaryKeyRelatedSerializerField(PrimaryKeyRelatedField):
    def __init__(self, **kwargs):
        self.serializer = kwargs.pop('serializer', None)

        if not self.serializer:
            raise Exception("PrimaryKeyRelatedSerializerField must define a 'serializer' attribute.")

        super(PrimaryKeyRelatedSerializerField, self).__init__(**kwargs)

    def to_representation(self, value):
        return self.serializer(self.queryset.get(pk=value.pk)).data


class KeyValueChoiceField(Field):
    default_error_messages = {
        'invalid_choice': _('"{input}" is not a valid choice.')
    }
    html_cutoff = None
    html_cutoff_text = _('More than {count} items...')

    def __init__(self, choices, **kwargs):
        self.choices = choices
        self.html_cutoff = kwargs.pop('html_cutoff', self.html_cutoff)
        self.html_cutoff_text = kwargs.pop('html_cutoff_text', self.html_cutoff_text)

        self.allow_blank = kwargs.pop('allow_blank', False)

        super(KeyValueChoiceField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        if data == '' and self.allow_blank:
            return ''

        try:
            return self.choice_strings_to_values[six.text_type(data)]
        except KeyError:
            self.fail('invalid_choice', input=data)

    def to_representation(self, value):
        if value in ('', None):
            return value
        return {
            'key': six.text_type(value),
            'value': self.choices[value]
        }

    def iter_options(self):
        """
        Helper method for use with templates rendering select widgets.
        """
        return iter_options(
            self.grouped_choices,
            cutoff=self.html_cutoff,
            cutoff_text=self.html_cutoff_text
        )

    def _get_choices(self):
        return self._choices

    def _set_choices(self, choices):
        self.grouped_choices = to_choices_dict(choices)
        self._choices = flatten_choices_dict(self.grouped_choices)

        # Map the string representation of choices to the underlying value.
        # Allows us to deal with eg. integer choices while supporting either
        # integer or string input, but still get the correct datatype out.
        self.choice_strings_to_values = {
            six.text_type(key): key for key in self.choices
        }

    choices = property(_get_choices, _set_choices)


def camel_to_snake(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def response_serializer(serializer,
                        object_class=None,
                        response_name=None,
                        pk=None,
                        data=None,
                        partial=False,
                        many=False,
                        obj=None,
                        context=None,
                        request=None,
                        post_is_valid_actions=None,
                        post_save_actions=None,
                        post_is_invalid_actions=None,
                        post_get_actions=None,
                        pre_validation_actions=None,
                        check_organisation=False):

    if not response_name:
        if object_class:
            response_name = str(object_class.__module__).split('.')[0][:-1].lower()
        elif obj:
            try:
                response_name = camel_to_snake(obj[0].__class__.__name__) + 's'
            except TypeError:
                response_name = camel_to_snake(obj.__class__.__name__)

    if pk:
        try:
            obj = object_class.objects.get(pk=pk)
        except object_class.DoesNotExist:
            raise Http404

        if check_organisation:
            organisation = get_organisation_by_user(request.user)

            if obj.organisation != organisation:
                raise Http404

    if isinstance(data, dict):
        if pre_validation_actions:
            for action in pre_validation_actions:
                response = action(request, data, obj)
                if isinstance(response, JsonResponse):
                    return response

        if obj:
            serializer = serializer(instance=obj, data=data, partial=partial, context=context)
            response_status = status.HTTP_200_OK
        else:
            serializer = serializer(data=data, context=context)
            response_status = status.HTTP_201_CREATED

        if serializer.is_valid():
            if post_is_valid_actions:
                for action in post_is_valid_actions:
                    response = action(request, data, obj)
                    if isinstance(response, JsonResponse):
                        return response

            serializer.save()

            if post_save_actions:
                for action in post_save_actions:
                    response = action(request, data, obj)
                    if isinstance(response, JsonResponse):
                        return response

            return JsonResponse(data={response_name: serializer.data},
                                status=response_status)

        if post_is_invalid_actions:
            for action in post_is_invalid_actions:
                response = action(request, data, obj)
                if isinstance(response, JsonResponse):
                    return response

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)

    else:
        if obj:
            serializer = serializer(obj, many=many, context=context)
        else:
            serializer = serializer(object_class, many=many, context=context)
        if post_get_actions:
            for action in post_get_actions:
                response = action(request, data, obj)
                if isinstance(response, JsonResponse):
                    return response

        return JsonResponse(data={response_name: serializer.data})
