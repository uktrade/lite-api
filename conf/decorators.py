from django.http import Http404, HttpResponseForbidden
from functools import wraps

from applications.libraries.get_applications import get_application


def only_application_type(request_method_list, filter_by_users_organisation=False, return_draft=True):
    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            if 'pk' in kwargs:
                draft_id = kwargs.pop('pk')
            elif 'application' in request.request.data:
                draft_id = request.request.data['application']
            else:
                raise Http404

            org_id = request.request.user.organisation.id if filter_by_users_organisation else None
            draft = get_application(draft_id, organisation_id=org_id)

            if draft.licence_type not in request_method_list:
                raise Http404

            if return_draft:
                kwargs['draft'] = draft

            return func(request, *args, **kwargs)

        return inner

    return decorator


def authorised_user_type(authorised_user_type):
    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            if not isinstance(request.request.user, authorised_user_type):
                return HttpResponseForbidden()
            return func(request, *args, **kwargs)

        return inner

    return decorator
