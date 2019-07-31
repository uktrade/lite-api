import json

from reversion.models import Revision
from reversion.models import Version

from static.statuses.enums import CaseStatusEnum
from cases.models import CaseNote
from static.statuses.libraries.get_case_status import get_case_status_from_status, get_case_status_from_pk
from users.libraries.get_user import get_user_by_pk
from users.models import ExporterUser
from users.serializers import BaseUserViewSerializer

CHANGE = 'change'
CASE_NOTE = 'case_note'
CHANGE_FLAGS = 'change_case_flags'


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

    data = json.loads(version.serialized_data)[0]['fields']
    if _revision_object.comment:
        try:
            comment = json.loads(_revision_object.comment)
            if 'flags' in comment:
                data['flags'] = comment['flags']
                activity_type = CHANGE_FLAGS
        except ValueError:
            comment = _revision_object.comment
            activity_type = CHANGE
        data['comment'] = comment
    else:
        activity_type = CHANGE

    if activity_type == CHANGE and 'flags' in data:
        return None

    if isinstance(user, ExporterUser) \
            and activity_type == CHANGE \
            and data['status'] == str(get_case_status_from_status(CaseStatusEnum.SUBMITTED).pk):
        return None

    if activity_type == CHANGE and 'status' in data:
        data['status'] = get_case_status_from_pk(data['status']).status

    return _activity_item(activity_type,
                          _revision_object.date_created,
                          BaseUserViewSerializer(user).data,
                          data)
