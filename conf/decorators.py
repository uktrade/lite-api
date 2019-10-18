from django.http import Http404, HttpResponseForbidden
from functools import wraps

from applications.libraries.get_applications import get_application
from applications.models import BaseApplication
from users.models import ExporterUser


def _get_application(request, kwargs):
    if 'pk' in kwargs:
        application = get_application(kwargs.pop('pk'))
    elif 'application' in request.request.data:
        application = get_application(request.request.data['application'])
    elif 'application' in kwargs and isinstance(kwargs['application'], BaseApplication):
        application = kwargs['application']
    else:
        raise Http404

    kwargs['application'] = application

    return application


def only_application_type(licence_type):
    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            application = _get_application(request, kwargs)

            if application.licence_type != licence_type:
                raise Http404

            return func(request, *args, **kwargs)

        return inner

    return decorator


def authorised_user_type(user_type):
    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            if not isinstance(request.request.user, user_type):
                return HttpResponseForbidden()

            if isinstance(request.request.user, ExporterUser):
                application = _get_application(request, kwargs)
                if application.organisation.id != request.request.user.organisation.id:
                    return HttpResponseForbidden()

            return func(request, *args, **kwargs)

        return inner

    return decorator
