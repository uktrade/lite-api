from django.http import Http404

from cases.models import Case


def get_case_flags_from_case(case):
    """
    Returns all the case flags assigned to a case
    """
    return Case.objects.filter(pk=case).first()
