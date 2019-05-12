from django.http import Http404

from cases.models import CaseNote


def get_case_note(pk):
    try:
        return CaseNote.objects.get(pk=pk)
    except CaseNote.DoesNotExist:
        raise Http404


def get_case_notes_from_case(case):
    return CaseNote.objects.filter(case=case).order_by('-created_at')
