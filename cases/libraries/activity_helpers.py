import json

from django.db.models import Q
from reversion.models import Revision
from reversion.models import Version

from cases.models import CaseNote, EcjuQuery
from goods.models import Good
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_from_status, get_case_status_from_pk
from users.libraries.get_user import get_user_by_pk
from users.models import ExporterUser
from users.serializers import BaseUserViewSerializer

CHANGE = 'change'
CASE_NOTE = 'case_note'
ECJU_QUERY = 'ecju_query'
CHANGE_CASE_FLAGS = 'change_case_flags'
CHANGE_GOOD_FLAGS = 'change_good_flags'


def _activity_item(activity_type, date, user, data, status=None):
    data = {
        'type': activity_type,
        'date': date,
        'user': user,
        'data': data,
    }
    if status:
        data['status'] = status
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


def convert_ecju_query_to_activity(ecju_query: EcjuQuery):
    """
    Converts an ecju_query to a dict suitable for the case activity list
    """
    user = get_user_by_pk(ecju_query.raised_by_user)

    return _activity_item(ECJU_QUERY,
                          ecju_query.created_at,
                          BaseUserViewSerializer(user).data,
                          ecju_query.question)


def convert_case_reversion_to_activity(version: Version):
    """
    Converts an audit item to a dict suitable for the case activity list
    """
    revision_object = Revision.objects.get(id=version.revision_id)
    user = get_user_by_pk(revision_object.user.id)
    activity = json.loads(version.serialized_data)[0]['fields']
    activity_type = CHANGE
    data = {}

    # Ignore the exporter user's `submitted` status and `case-created` audits
    # (these are created when a case has first been made)
    if isinstance(user, ExporterUser) and ('type' in activity or activity['status'] == str(
            get_case_status_from_status(CaseStatusEnum.SUBMITTED).pk)):
        return None

    try:
        comment = json.loads(revision_object.comment)
        if 'flags' in comment:
            data['flags'] = comment['flags']
            activity_type = CHANGE_CASE_FLAGS
    except ValueError:
        if activity_type == CHANGE and 'status' in activity:
            data['status'] = get_case_status_from_pk(activity['status']).status

    return _activity_item(activity_type,
                          revision_object.date_created,
                          BaseUserViewSerializer(user).data,
                          data)


def convert_good_reversion_to_activity(version: Version, good: Good):
    """
    Converts an audit item to a dict suitable for the case activity list
    """
    revision_object = Revision.objects.get(id=version.revision_id)
    user = get_user_by_pk(revision_object.user.id)
    activity_type = CHANGE
    data = {}

    try:
        comment = json.loads(revision_object.comment)
        if 'flags' in comment:
            data['flags'] = comment['flags']
            data['good'] = good.description
            activity_type = CHANGE_GOOD_FLAGS
    except ValueError:
        return None
    return _activity_item(activity_type,
                          revision_object.date_created,
                          BaseUserViewSerializer(user).data,
                          data)


def add_items_to_activity(activity, object):
    version_records = Version.objects.filter(Q(object_id=object.pk))
    for version in version_records:
        activity_item = convert_good_reversion_to_activity(version, object)
        if activity_item:
            activity.append(activity_item)
