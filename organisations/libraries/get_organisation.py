from conf.authentication import ORGANISATION_ID
from conf.exceptions import NotFoundError
from organisations.models import Organisation


def get_organisation_by_pk(pk):
    try:
        return Organisation.objects.get(pk=pk)
    except Organisation.DoesNotExist:
        raise NotFoundError({"organisation": "Organisation not found - " + str(pk)})


def get_request_user_organisation_id(request):
    return request.META.get(ORGANISATION_ID)


def get_request_user_organisation(request):
    org_id = get_request_user_organisation_id(request)
    return get_organisation_by_pk(org_id)
