from api.audit_trail.models import Audit
from api.audit_trail.service import serialize_case_activity

from api.users.models import BaseUser


def retrieve_latest_activity(case):
    activities_qs = Audit.objects.get_latest_activities([case.id], 1)
    # Django merges and orders both action and target objects so no need for additional filtering
    latest_activity = activities_qs.first()
    if not latest_activity:
        return
    actor = BaseUser.objects.select_related("exporteruser", "govuser", "govuser__team").get(
        id=latest_activity.actor_object_id
    )
    return serialize_case_activity(latest_activity, actor)
