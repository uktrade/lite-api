from cases.models import CaseNote
from conf.exceptions import NotFoundError


def get_case_note(pk):
    """
    Returns a case note or returns a 404 on failure
    """
    try:
        return CaseNote.objects.get(pk=pk)
    except CaseNote.DoesNotExist:
        raise NotFoundError({"case_note": "Case Note not found"})


def get_case_notes_from_case(case, only_show_notes_visible_to_exporter):
    """
    Returns all the case notes from a case
    If is_visible_to_exporter is True, then only show case notes that are visible to exporters
    """
    if only_show_notes_visible_to_exporter:
        return CaseNote.objects.filter(case=case, is_visible_to_exporter=True).order_by("-created_at")
    else:
        return CaseNote.objects.filter(case=case).order_by("-created_at")
