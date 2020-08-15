from api.cases.models import CaseNote
from api.conf.exceptions import NotFoundError


def get_case_note(pk):
    """
    Returns a case note or returns a 404 on failure
    """
    try:
        return CaseNote.objects.get(pk=pk)
    except CaseNote.DoesNotExist:
        raise NotFoundError({"case_note": "Case Note not found"})


def get_case_notes_from_case(case_id, only_show_notes_visible_to_exporter=False):
    """
    Returns all the case notes from a case
    If only_show_notes_visible_to_exporter is True, then only show case notes that are visible to exporters
    """
    if only_show_notes_visible_to_exporter:
        return (
            CaseNote.objects.select_related("user")
            .filter(case_id=case_id, is_visible_to_exporter=True)
            .order_by("-created_at")
        )
    else:
        return CaseNote.objects.select_related("user").filter(case_id=case_id).order_by("-created_at")
