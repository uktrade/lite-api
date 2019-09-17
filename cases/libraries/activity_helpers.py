from cases.libraries.activity_types import CaseActivityType
from cases.models import CaseActivity


def convert_case_notes_to_activity(case_notes):
    """
    Converts case notes to CaseActivity items
    """
    return_value = []

    for case_note in case_notes:
        return_value.append(CaseActivity.create(activity_type=CaseActivityType.CASE_NOTE,
                                                case=case_note.case,
                                                user=case_note.user,
                                                additional_text=case_note.text,
                                                created_at=case_note.created_at,
                                                save_object=False))

    return return_value
