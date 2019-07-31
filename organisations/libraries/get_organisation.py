from django.http import Http404

from conf.exceptions import NotFoundError
from organisations.models import Organisation
from users.models import ExporterUser


def get_organisation_by_pk(pk):
    try:
        return Organisation.objects.get(pk=pk)
    except Organisation.DoesNotExist:
        raise NotFoundError({'organisation': 'Organisation not found - ' + str(pk)})


def get_organisation_by_user(user: ExporterUser):
    if not user.organisation:
        raise Http404

    return user.organisation
