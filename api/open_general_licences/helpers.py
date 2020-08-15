import datetime

from django.utils import timezone

from api.conf.exceptions import NotFoundError
from licences.helpers import get_licence_reference_code
from licences.models import Licence
from api.open_general_licences.models import OpenGeneralLicenceCase


def get_open_general_licence(pk):
    from api.open_general_licences.models import OpenGeneralLicence

    try:
        return OpenGeneralLicence.objects.get(pk=pk)
    except OpenGeneralLicence.DoesNotExist:
        raise NotFoundError({"open_general_licence": "Open general licence not found - " + str(pk)})


def get_open_general_licence_duration():
    """
    Should calculate a duration equivalent to ending in
    December 2076 as this is what spire did
    """
    start_date = timezone.localtime().date()
    end_date = datetime.date(2076, 12, 31)
    return (end_date.year - start_date.year) * 12 + end_date.month - start_date.month


def issue_open_general_licence(ogel: OpenGeneralLicenceCase):
    licence = Licence.objects.create(
        reference_code=get_licence_reference_code(ogel.reference_code),
        case_id=ogel.id,
        start_date=timezone.localtime().date(),
        duration=get_open_general_licence_duration(),
    )
    licence.issue()
    return licence
