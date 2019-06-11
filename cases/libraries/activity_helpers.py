import json

from reversion.models import Revision, Version

from cases.models import CaseNote


CHANGE = 'change'
CASE_NOTE = 'case_note'


def _activity_item(activity_type, date, user_id, data):
    data = {
        'type': activity_type,
        'date': date,
        'user_id': user_id,
        'data': data
    }
    return data


def convert_case_note_to_activity(case_note: CaseNote):
    """
    Converts a case note to a dict suitable for the case activity list
    """
    return _activity_item(CASE_NOTE,
                          case_note.created_at,
                          None,  # TODO: Case Note doesn't have a user field yet (User object doesn't exist, see LT-936)
                          case_note.text)


def convert_audit_to_activity(version: Version):
    """
    Converts an audit item to a dict suitable for the case activity list
    """
    _revision_object = Revision.objects.get(id=version.revision_id)
    return _activity_item(CHANGE,
                          _revision_object.date_created,
                          _revision_object.user_id,
                          json.loads(version.serialized_data)[0]['fields'])
