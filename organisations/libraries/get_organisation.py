from conf.exceptions import NotFoundError
from organisations.models import Organisation


def get_organisation_by_pk(pk):
    try:
        return Organisation.objects.get(pk=pk)
    except Organisation.DoesNotExist:
        raise NotFoundError({"organisation": "Organisation not found - " + str(pk)})
