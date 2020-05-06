from functools import wraps

from django.http import JsonResponse
from rest_framework import status

from applications.enums import GoodsTypeCategory
from applications.libraries.case_status_helpers import get_case_statuses
from applications.libraries.get_applications import get_application
from applications.models import BaseApplication
from cases.enums import CaseTypeSubTypeEnum
from lite_content.lite_api import strings
from parties.enums import PartyType
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

            if application.case_type.sub_type not in application_types:
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
    A Major editable state is either APPLICANT_EDITING or DRAFT
    """

    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            application = _get_application(request, kwargs)

            if not application.is_major_editable():
                return JsonResponse(
                    data={"errors": [strings.Applications.Generic.NOT_POSSIBLE_ON_MINOR_EDIT]},
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

            if not application.is_editable():
                return JsonResponse(
                    data={"errors": [strings.Applications.Generic.READ_ONLY_CASE_CANNOT_PERFORM_OPERATION_ERROR]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return func(request, *args, **kwargs)

        return inner

    return decorator


def application_in_non_readonly_state():
    """ Validate that an application is not in a readonly state. """

    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            application = _get_application(request, kwargs)

            if is_case_status_draft(application.status.status) and application.status.status in get_case_statuses(
                read_only=True
            ):
                return JsonResponse(
                    data={"errors": [f"Application status {application.status.status} is read-only."]},
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
                    application.case_type.sub_type == CaseTypeSubTypeEnum.HMRC
                    and application.hmrc_organisation.id != request.request.user.organisation.id
                ) or (
                    application.case_type.sub_type != CaseTypeSubTypeEnum.HMRC
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


def allowed_party_type_for_open_application_goodstype_category():
    """
    Will restrict any parties being created on open applications based on goodstype category
    """

    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            application = _get_application(request, kwargs)

            party_type = request.request.data.get("type")

            if application.case_type.sub_type == CaseTypeSubTypeEnum.OPEN and party_type:
                if (
                    application.goodstype_category == GoodsTypeCategory.MILITARY
                    and party_type == PartyType.ULTIMATE_END_USER
                ):
                    pass
                elif (
                    application.goodstype_category == GoodsTypeCategory.CRYPTOGRAPHIC
                    and party_type == PartyType.THIRD_PARTY
                ):
                    pass
                else:
                    return JsonResponse(
                        data={"errors": ["This type of party can not be added to this type of open application"]},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            return func(request, *args, **kwargs)

        return inner

    return decorator
