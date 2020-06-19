from conf.exceptions import NotFoundError
from open_general_licences.models import OpenGeneralLicence


def get_open_general_licence(pk):
    try:
        return OpenGeneralLicence.objects.get(pk=pk)
    except OpenGeneralLicence.DoesNotExist:
        raise NotFoundError({"open_general_licence": "Open general licence not found - " + str(pk)})
