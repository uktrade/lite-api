from django.http import HttpResponseForbidden, HttpResponseNotFound, HttpResponseBadRequest
from functools import wraps

from applications.libraries.get_applications import get_application
from applications.models import BaseApplication
from static.statuses.enums import CaseStatusEnum
from users.models import ExporterUser


def _get_application(request, kwargs):
    if 'pk' in kwargs:
        application = get_application(kwargs.pop('pk'))
    elif 'application' in request.request.data:
        application = get_application(request.request.data['application'])
    elif 'application' in kwargs and isinstance(kwargs['application'], BaseApplication):
        application = kwargs['application']
    else:
        return HttpResponseNotFound()

    kwargs['application'] = application

    return application


def only_applications(licence_type, can_be_edited=False):
    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            application = _get_application(request, kwargs)

            if application.licence_type != licence_type:
                return HttpResponseBadRequest()

            if can_be_edited:
                if application.status and application.status != CaseStatusEnum.APPLICANT_EDITING:
                    return HttpResponseBadRequest()

            return func(request, *args, **kwargs)

        return inner

    return decorator


def authorised_users(user_type):
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
