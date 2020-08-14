from uuid import UUID

from api.conf.authentication import ORGANISATION_ID
from api.conf.exceptions import NotFoundError
from api.organisations.models import Organisation


def get_organisation_by_pk(pk):
    try:
        return Organisation.objects.get(pk=pk)
    except Organisation.DoesNotExist:
        raise NotFoundError({"organisation": "Organisation not found - " + str(pk)})


def get_request_user_organisation_id(request):
    org_token = request.META.get(ORGANISATION_ID)
    if isinstance(org_token, str):
        return UUID(org_token)
    else:
        return org_token


def get_request_user_organisation(request):
    org_id = get_request_user_organisation_id(request)
    return get_organisation_by_pk(org_id)
