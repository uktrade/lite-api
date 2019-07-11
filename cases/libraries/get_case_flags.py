from django.http import Http404

from cases.models import CaseFlags


def get_case_flags_from_case(case):
    """
    Returns all the case flags assigned to a case
    """
    return CaseFlags.objects.filter(case=case).prefetch_related('flag').all()
