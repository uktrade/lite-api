import datetime

from django.utils import timezone

from conf.exceptions import NotFoundError


def get_open_general_licence(pk):
    from open_general_licences.models import OpenGeneralLicence

    try:
        return OpenGeneralLicence.objects.get(pk=pk)
    except OpenGeneralLicence.DoesNotExist:
        raise NotFoundError({"open_general_licence": "Open general licence not found - " + str(pk)})


def get_open_general_licence_duration():
    """
    Should calculate a duration equivalent to ending in
    December 2067 as this is what spire did
    """
    start_date = timezone.now().date()
    end_date = datetime.date(2076, 12, 31)
    return (end_date.year - start_date.year) * 12 + end_date.month - start_date.month
