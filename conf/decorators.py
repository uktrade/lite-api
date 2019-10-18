from django.http import Http404, HttpResponseForbidden
from functools import wraps

from applications.libraries.get_applications import get_application


def only_application_type(licence_type, filter_by_user_org=True, return_application=True):
    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            if 'pk' in kwargs:
                application_id = kwargs.pop('pk')
            elif 'application' in request.request.data:
                application_id = request.request.data['application']
            else:
                raise Http404

            org_id = request.request.user.organisation.id if filter_by_user_org else None
            application = get_application(application_id, organisation_id=org_id)

            if application.licence_type != licence_type:
                raise Http404

            if return_application:
                kwargs['application'] = application

            return func(request, *args, **kwargs)

        return inner

    return decorator


def authorised_user_type(user_type):
    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            if not isinstance(request.request.user, user_type):
                return HttpResponseForbidden()
            return func(request, *args, **kwargs)

        return inner

    return decorator
