from conf.exceptions import NotFoundError
from open_general_licences.models import OpenGeneralLicenceCase


def get_open_general_export_licence_case(pk):
    try:
        return OpenGeneralLicenceCase.objects.get(pk=pk)
    except OpenGeneralLicenceCase.DoesNotExist:
        raise NotFoundError({"open_general_licence_case": "Open general licence case not found - " + str(pk)})
