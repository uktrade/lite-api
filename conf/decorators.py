from django.http import Http404
from functools import wraps

from applications.libraries.get_applications import get_application


def only_draft_types(request_method_list, return_draft=True):
    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            if 'pk' in kwargs:
                draft_id = kwargs.pop('pk')
            elif 'application' in request.request.data:
                draft_id = request.request.data['application']
            else:
                raise Http404

            draft = get_application(draft_id, submitted=False)
            if draft.licence_type not in request_method_list:
                raise Http404
            if return_draft:
                kwargs['draft'] = draft
            return func(request, *args, **kwargs)

        return inner

    return decorator
