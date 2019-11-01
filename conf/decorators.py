from functools import wraps

from django.http import JsonResponse
from rest_framework import status

from applications.enums import ApplicationType
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
        return JsonResponse(data={'errors': ['Application was not found']},
                            status=status.HTTP_404_NOT_FOUND)

    kwargs['application'] = application

    return application


def application_type(application_type):
    """
    Checks if application is the correct type for the request
    """

    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            application = _get_application(request, kwargs)

            if application.application_type != application_type:
                return JsonResponse(data={'errors': [f'This operation can only be used on applications of type '
                                                     f'`{application_type}`']},
                                    status=status.HTTP_400_BAD_REQUEST)

            return func(request, *args, **kwargs)

        return inner

    return decorator


def application_in_major_editable_state():
    """
    Checks if application is in a major-editable state;
    A Major editable state is either APPLICANT_EDITING or NONE (An un-submitted application)
    """

    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            application = _get_application(request, kwargs)

            if application.status and application.status.status != CaseStatusEnum.APPLICANT_EDITING:
                return JsonResponse(data={'errors': [f'You can only perform this operation when the application is '
                                                     f'in a `draft` or `{CaseStatusEnum.APPLICANT_EDITING}` state']},
                                    status=status.HTTP_400_BAD_REQUEST)

            return func(request, *args, **kwargs)

        return inner

    return decorator


def authorised_users(user_type):
    """
    Checks if the user is the correct type and if they have access to the application being requested
    """

    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            if not isinstance(request.request.user, user_type):
                return JsonResponse(data={'errors': ['You are not authorised to perform this operation']},
                                    status=status.HTTP_403_FORBIDDEN)

            if isinstance(request.request.user, ExporterUser):
                application = _get_application(request, kwargs)
                if application.application_type == ApplicationType.HMRC_QUERY:
                    if application.hmrc_organisation.id != request.request.user.organisation.id:
                        return JsonResponse(data={'errors': ['You can only perform this operation on an application '
                                                             'that has been opened within your organisation']},
                                            status=status.HTTP_403_FORBIDDEN)
                    if application.submitted_at is not None:
                        return JsonResponse(
                            data={'errors': ['You can only perform this operation on an application '
                                             'that has not been submitted']},
                            status=status.HTTP_403_FORBIDDEN)

                elif application.organisation.id != request.request.user.organisation.id:
                    return JsonResponse(data={'errors': ['You can only perform this operation on an application '
                                                         'that has been opened within your organisation']},
                                        status=status.HTTP_403_FORBIDDEN)

            return func(request, *args, **kwargs)

        return inner

    return decorator
