from datetime import timedelta
from typing import List, Dict

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.db.models import Value
from django.db.models.functions import Concat
from django.utils import timezone

from audit_trail.models import Audit
from cases.enums import CaseTypeEnum
from cases.models import Case
from cases.sla import working_days_in_range
from cases.views.search.queue import SearchQueue
from static.statuses.enums import CaseStatusEnum
from users.enums import UserStatuses
from users.models import GovUser


def get_case_status_list() -> List[Dict]:
    return CaseStatusEnum.as_list()


def get_case_type_type_list() -> List[Dict]:
    return CaseTypeEnum.case_types_to_representation()


def get_search_queues(user):
    return SearchQueue.all(user=user)


def get_gov_users_list():
    return [
        {"key": full_name.lower(), "value": full_name}
        for full_name in GovUser.objects.filter(status=UserStatuses.ACTIVE)
        .annotate(full_name=Concat("first_name", Value(" "), "last_name"))
        .values_list("full_name", flat=True)
    ]


def populate_is_recently_updated(cases: Dict):
    """
    Given a dictionary of cases, annotate each one with the field "is_recently_updated"
    If the case was submitted less than settings.RECENTLY_UPDATED_DAYS ago, set the field to True
    If the case was not, check that it has audit activity less than settings.RECENTLY_UPDATED_DAYS
    ago and return True, else return False
    """
    now = timezone.now()
    recent_audits = (
        Audit.objects.filter(
            target_content_type=ContentType.objects.get_for_model(Case),
            target_object_id__in=[case["id"] for case in cases],
            actor_content_type=ContentType.objects.get_for_model(GovUser),
            created_at__gt=now - timedelta(days=settings.RECENTLY_UPDATED_DAYS),
        )
        .values("target_object_id")
        .annotate(Count("target_object_id"))
    )

    audit_dict = {a["target_object_id"]: a["target_object_id__count"] for a in recent_audits}

    for case in cases:
        case["is_recently_updated"] = (
            working_days_in_range(case["submitted_at"], now) < settings.RECENTLY_UPDATED_DAYS
            or audit_dict.get(case["id"], 0) > 0
        )
