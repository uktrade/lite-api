from addresses.models import Address
from conf.exceptions import NotFoundError


def get_address(pk):
    try:
        return Address.objects.get(pk=pk)
    except Address.DoesNotExist:
        raise NotFoundError({"address": "Address not found - " + str(pk)})
