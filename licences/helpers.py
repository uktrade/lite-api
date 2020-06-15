from licences.models import Licence
from string import ascii_uppercase


def get_reference_code(application_reference):
    total_reference_codes = Licence.objects.filter(reference_code__icontains=application_reference).count()
    return (
        f"{application_reference}/{ascii_uppercase[total_reference_codes-1]}"
        if total_reference_codes != 0
        else application_reference
    )
