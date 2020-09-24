from typing import Callable, Type, Union, List

from functools import wraps

from django.http import JsonResponse, Http404
from rest_framework import status

from api.applications.enums import GoodsTypeCategory
from api.applications.libraries.get_applications import get_application
from api.applications.models import BaseApplication, HmrcQuery
from api.cases.enums import CaseTypeSubTypeEnum
from lite_content.lite_api import strings
from api.organisations.libraries.get_organisation import get_request_user_organisation_id
from api.parties.enums import PartyType
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
        return JsonResponse(data={"errors": ["Application was not found"]}, status=status.HTTP_404_NOT_FOUND,)


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
            sub_type = _get_application(request, kwargs).values_list("case_type__sub_type", flat=True)[0]

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


def application_in_state(is_editable: bool = False, is_major_editable: bool = False) -> Callable:
    """
    Checks if application is in an editable or major-editable state
    """

    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            application_status = _get_application(request, kwargs).values_list("status__status", flat=True)[0]

            if is_editable and application_status in CaseStatusEnum.read_only_statuses():
                return JsonResponse(
                    data={
                        "errors": {
                            "non_field_errors": [
                                strings.Applications.Generic.INVALID_OPERATION_FOR_READ_ONLY_CASE_ERROR
                            ]
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if is_major_editable and application_status not in CaseStatusEnum.major_editable_statuses():
                return JsonResponse(
                    data={
                        "errors": {
                            "non_field_errors": [
                                strings.Applications.Generic.INVALID_OPERATION_FOR_NON_DRAFT_OR_MAJOR_EDIT_CASE_ERROR
                            ]
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return func(request, *args, **kwargs)

        return inner

    return decorator


def authorised_to_view_application(user_type: Union[Type[GovUser], Type[ExporterUser]]) -> Callable:
    """
    Checks if the user is the correct type and if they have access to the application being requested
    """

    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
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
                pk = _get_application_id(request, kwargs)
                organisation_id = get_request_user_organisation_id(request.request)
                required_application_details = _get_application(request, kwargs).values(
                    "case_type__sub_type", "organisation_id"
                )[0]

                if required_application_details["case_type__sub_type"] == CaseTypeSubTypeEnum.HMRC:
                    has_access = HmrcQuery.objects.filter(pk=pk, hmrc_organisation=organisation_id).exists()
                else:
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


def allowed_party_type_for_open_application_goodstype_category() -> Callable:
    """
    Will restrict any parties being created on open applications based on goodstype category
    """

    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            application_id = _get_application_id(request, kwargs)
            application = get_application(application_id)

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
                elif party_type == PartyType.END_USER:
                    pass
                else:
                    return JsonResponse(
                        data={"errors": ["This type of party can not be added to this type of open application"]},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            return func(request, *args, **kwargs)

        return inner

    return decorator
