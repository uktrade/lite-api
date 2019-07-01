from django.http import Http404

from cases.models import CaseNote


def get_case_note(pk):
    """
    Returns a case note or returns a 404 on failure
    """
    try:
        return CaseNote.objects.get(pk=pk)
    except CaseNote.DoesNotExist:
        raise Http404


def get_case_notes_from_case(case):
    """
    Returns all the case notes from a case
    """
    return CaseNote.objects.filter(case=case).order_by('-created_at')
