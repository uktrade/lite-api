import json

from reversion.models import Revision, Version

from cases.models import CaseNote
from gov_users.models import GovUserRevisionMeta

CHANGE = 'change'
CASE_NOTE = 'case_note'
CHANGE_FLAGS = 'change_case_flags'


def _activity_item(activity_type, date, user, data):
    data = {
        'type': activity_type,
        'date': date,
        'user': {
            'id': user['id'],
            'email': user['email'],
            'first_name': user['first_name'],
            'last_name': user['last_name'],
            'group': 'GOV USER',
        },
        'data': data
    }
    return data


def convert_case_note_to_activity(case_note: CaseNote):
    """
    Converts a case note to a dict suitable for the case activity list
    """
    return _activity_item(CASE_NOTE,
                          case_note.created_at,
                          {
                              'id': case_note.user.id,
                              'email': case_note.user.email,
                              'first_name': case_note.user.first_name,
                              'last_name': case_note.user.last_name,
                          },
                          case_note.text)


def convert_audit_to_activity(version: Version):
    """
    Converts an audit item to a dict suitable for the case activity list
    """
    _revision_object = Revision.objects.get(id=version.revision_id)
    try:
        gov_user = GovUserRevisionMeta.objects.get(revision_id=version.revision_id).gov_user
    except GovUserRevisionMeta.DoesNotExist:
        return

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

    return _activity_item(activity_type,
                          _revision_object.date_created,
                          {
                              'id': gov_user.id,
                              'email': gov_user.email,
                              'first_name': gov_user.first_name,
                              'last_name': gov_user.last_name,
                          },
                          data)
