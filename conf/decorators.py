from functools import wraps

from django.http import Http404

from applications.libraries.get_applications import get_draft


def only_application_types(request_method_list):

    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            draft = get_draft(kwargs.pop('pk'))
            if draft.licence_type not in request_method_list:
                raise Http404
            kwargs['draft'] = draft
            return func(request, *args, **kwargs)

        return inner

    return decorator
