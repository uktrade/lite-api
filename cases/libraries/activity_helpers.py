import json

from reversion.models import Revision, Version

from cases.models import CaseNote

CHANGE = 'change'
CASE_NOTE = 'case_note'


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
                          # TODO: Case Note doesn't have a user field yet (User object doesn't exist, see LT-936)
                          {
                              'id': '1234',
                              'email': 'test@mail.com',
                              'first_name': 'Matthew',
                              'last_name': 'Berninger',
                          },
                          case_note.text)


def convert_audit_to_activity(version: Version):
    """
    Converts an audit item to a dict suitable for the case activity list
    """
    _revision_object = Revision.objects.get(id=version.revision_id)
    return _activity_item(CHANGE,
                          _revision_object.date_created,
                          {
                              'id': _revision_object.user_id,
                              'email': 'test@mail.com',
                              'first_name': 'Matthew',
                              'last_name': 'Berninger',
                          },
                          json.loads(version.serialized_data)[0]['fields'])
