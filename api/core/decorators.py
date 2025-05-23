from typing import Callable, Type, Union, List

from functools import wraps
from uuid import UUID

from django.http import JsonResponse, Http404
from rest_framework import status

from api.applications.models import BaseApplication
from api.licences.enums import LicenceStatus
from api.licences.models import Licence
from lite_content.lite_api import strings
from api.organisations.libraries.get_organisation import get_request_user_organisation_id
from api.staticdata.statuses.enums import CaseStatusEnum
from api.users.models import GovUser, ExporterUser
from rest_framework.views import APIView
from api.users.enums import UserType


def _get_application_id(request: APIView, kwargs):
    if "pk" in kwargs:
        return kwargs.get("pk")
    elif "application" in request.request.data:
        return request.request.data["application"]
    else:
        return JsonResponse(
            data={"errors": ["Application was not found"]},
            status=status.HTTP_404_NOT_FOUND,
        )


def _get_application(request: APIView, kwargs):
    pk = _get_application_id(request, kwargs)
    result = BaseApplication.objects.filter(pk=pk)
    if not result.exists():
        raise Http404
    else:
        return result


def allowed_application_types(application_types: List[str]) -> Callable:
    """
    Checks if application is the correct type for the request
    """

    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            sub_type = _get_application(request, kwargs).values_list("case_type__reference", flat=True)[0]

            if sub_type not in application_types:
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


def application_in_status(status_check_func):
    @wraps(status_check_func)
    def decorator(view_func):
        @wraps(view_func)
        def inner(request, *args, **kwargs):
            application_status = _get_application(request, kwargs).values_list("status__status", flat=True)[0]
            has_status, error = status_check_func(application_status)
            if has_status:
                return view_func(request, *args, **kwargs)
            return JsonResponse(
                data={"errors": {"non_field_errors": [error]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return inner

    return decorator


@application_in_status
def application_is_editable(application_status):
    """
    Checks if application is editable
    """
    return (
        CaseStatusEnum.is_editable(application_status),
        strings.Applications.Generic.INVALID_OPERATION_FOR_READ_ONLY_CASE_ERROR,
    )


@application_in_status
def application_is_major_editable(application_status):
    """
    Checks if application is major editable
    """
    return (
        CaseStatusEnum.is_major_editable_status(application_status),
        strings.Applications.Generic.INVALID_OPERATION_FOR_NON_DRAFT_OR_MAJOR_EDIT_CASE_ERROR,
    )


@application_in_status
def application_can_invoke_major_edit(application_status):
    """
    Checks if application is in a state where a  major edit can be started
    """
    return (
        CaseStatusEnum.can_invoke_major_edit(application_status),
        strings.Applications.Generic.INVALID_OPERATION_FOR_NON_DRAFT_OR_MAJOR_EDIT_CASE_ERROR,
    )


def authorised_to_view_application(user_type: Union[Type[GovUser], Type[ExporterUser]]) -> Callable:
    """
    Checks if the user is the correct type and if they have access to the application being requested
    """

    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            # TODO: Wrong function signature. Should be (self, request, ..)
            base_user = request.request.user
            user = base_user
            if hasattr(base_user, "govuser"):
                user = base_user.govuser
            elif hasattr(base_user, "exporteruser"):
                user = base_user.exporteruser

            if not isinstance(user, user_type):
                return JsonResponse(
                    data={"errors": ["You are not authorised to perform this operation"]},
                    status=status.HTTP_403_FORBIDDEN,
                )

            if user.type != UserType.INTERNAL and user.type != UserType.EXPORTER:
                return JsonResponse(
                    data={"errors": ["You are not authorised to perform this operation"]},
                    status=status.HTTP_403_FORBIDDEN,
                )

            if user.type == UserType.EXPORTER:
                organisation_id = get_request_user_organisation_id(request.request)
                required_application_details = _get_application(request, kwargs).values(
                    "case_type__sub_type", "organisation_id"
                )[0]

                has_access = required_application_details["organisation_id"] == organisation_id
                if not has_access:
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


def authorised_govuser_roles(user_role_ids: List[UUID]) -> Callable:
    """
    Checks if the user is the correct type and of correct role
    """

    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            user = request.request.user

            if hasattr(user, "govuser"):
                user = user.govuser
            elif not isinstance(user, GovUser) or not user.type == UserType.INTERNAL:
                return JsonResponse(
                    data={"errors": ["You are not authorised to perform this operation."]},
                    status=status.HTTP_403_FORBIDDEN,
                )

            if user.role.id not in user_role_ids:
                return JsonResponse(
                    data={"errors": ["The user must be in a specific role to perform this action."]},
                    status=status.HTTP_403_FORBIDDEN,
                )

            return func(request, *args, **kwargs)

        return inner

    return decorator


def licence_is_editable() -> Callable:
    """
    Will restrict licence updates to specefic criterion
    """

    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            licence_id = kwargs.get("pk")
            licence = Licence.objects.get(id=licence_id)
            # Check if License Status is Editable
            if not LicenceStatus.can_edit_status(licence.status):
                return JsonResponse(
                    data={"errors": ["The licence status is not editable."]},
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Check if Case is in finialised state
            if licence.case.status.status != CaseStatusEnum.FINALISED:
                return JsonResponse(
                    data={"errors": ["To edit a licence the case must be in a finalised state."]},
                    status=status.HTTP_403_FORBIDDEN,
                )
            return func(request, *args, **kwargs)

        return inner

    return decorator
