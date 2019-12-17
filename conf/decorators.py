from functools import wraps

from django.http import JsonResponse
from rest_framework import status

from lite_content.lite_api import cases
from applications.enums import ApplicationType
from applications.libraries.case_status_helpers import get_case_statuses
from applications.libraries.get_applications import get_application
from applications.models import BaseApplication
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.case_status_validate import is_case_status_draft
from users.models import ExporterUser


def _get_application(request, kwargs):
    if "pk" in kwargs:
        application = get_application(kwargs.pop("pk"))
    elif "application" in request.request.data:
        application = get_application(request.request.data["application"])
    elif "application" in kwargs and isinstance(kwargs["application"], BaseApplication):
        application = kwargs["application"]
    else:
        return JsonResponse(data={"errors": ["Application was not found"]}, status=status.HTTP_404_NOT_FOUND,)

    kwargs["application"] = application

    return application


def allowed_application_types(application_types: [str]):
    """
    Checks if application is the correct type for the request
    """

    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            application = _get_application(request, kwargs)

            if application.application_type not in application_types:
                return JsonResponse(
                    data={
                        "errors": [
                            "This operation can only be used "
                            "on applications of type: " + ", ".join(application_types)
                        ]
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

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

            if (
                not is_case_status_draft(application.status.status)
                and application.status.status != CaseStatusEnum.APPLICANT_EDITING
            ):
                return JsonResponse(
                    data={
                        "errors": [
                            f"You can only perform this operation when the application is "
                            f"in a `draft` or `{CaseStatusEnum.APPLICANT_EDITING}` state"
                        ]
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return func(request, *args, **kwargs)

        return inner

    return decorator


def application_in_editable_state():
    """ Check if an application is in an editable state. """

    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            application = _get_application(request, kwargs)

            if application.status.status in get_case_statuses(read_only=True):
                return JsonResponse(
                    data={"errors": [cases.System.READ_ONLY_CASE_CANNOT_PERFORM_OPERATION_ERROR]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

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
                return JsonResponse(
                    data={"errors": ["You are not authorised to perform this operation"]},
                    status=status.HTTP_403_FORBIDDEN,
                )

            if isinstance(request.request.user, ExporterUser):
                application = _get_application(request, kwargs)
                if (
                    application.application_type == ApplicationType.HMRC_QUERY
                    and application.hmrc_organisation.id != request.request.user.organisation.id
                ) or (
                    application.application_type != ApplicationType.HMRC_QUERY
                    and application.organisation.id != request.request.user.organisation.id
                ):
                    return JsonResponse(
                        data={
                            "errors": [
                                "You can only perform this operation on an application "
                                "that has been opened within your organisation"
                            ]
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )

            return func(request, *args, **kwargs)

        return inner

    return decorator
