from django.http import Http404

from cases.models import CaseFlags


def get_case_flags_from_case(case_id):
    """
    Returns all the case flags assigned to a case
    """
    return CaseFlags.objects.filter(case_id=case_id).only("flag_id")
