import json

from reversion.models import Revision
from reversion.models import Version

from cases.models import CaseNote
from users.libraries.get_user import get_user_by_pk
from users.serializers import BaseUserViewSerializer

CHANGE = 'change'
CASE_NOTE = 'case_note'


def _activity_item(activity_type, date, user, data, status=None):
    data = {
        'type': activity_type,
        'date': date,
        'user': user,
        'data': data,
        'status': status
    }
    return data


def convert_case_note_to_activity(case_note: CaseNote):
    """
    Converts a case note to a dict suitable for the case activity list
    """
    user = get_user_by_pk(case_note.user.id)

    return _activity_item(CASE_NOTE,
                          case_note.created_at,
                          BaseUserViewSerializer(user).data,
                          case_note.text,
                          status='Visible to exporter' if case_note.is_visible_to_exporter else None)


def convert_audit_to_activity(version: Version):
    """
    Converts an audit item to a dict suitable for the case activity list
    """
    _revision_object = Revision.objects.get(id=version.revision_id)
    user = get_user_by_pk(_revision_object.user.id)

    return _activity_item(CHANGE,
                          _revision_object.date_created,
                          BaseUserViewSerializer(user).data,
                          json.loads(version.serialized_data)[0]['fields'])
