from datetime import timedelta
from typing import List, Dict

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.db.models import Value
from django.db.models.functions import Concat
from django.utils import timezone

from applications.models import HmrcQuery
from audit_trail.models import Audit
from cases.enums import CaseTypeEnum, CaseTypeSubTypeEnum, AdviceType
from cases.models import Case
from common.dates import working_days_in_range, number_of_days_since, working_hours_in_range
from static.statuses.enums import CaseStatusEnum
from users.enums import UserStatuses
from users.models import GovUser


def get_case_status_list() -> List[Dict]:
    return CaseStatusEnum.as_list()


def get_case_type_type_list() -> List[Dict]:
    return CaseTypeEnum.case_types_to_representation()


def get_gov_users_list():
    return (
        GovUser.objects.filter(status=UserStatuses.ACTIVE)
        .annotate(full_name=Concat("first_name", Value(" "), "last_name"))
        .values("id", "full_name")
    )


def get_advice_types_list():
    return AdviceType.to_representation()


def populate_is_recently_updated(cases: List[Dict]):
    """
    Given a dictionary of cases, annotate each one with the field "is_recently_updated"
    If the case was submitted less than settings.RECENTLY_UPDATED_WORKING_DAYS ago, set the field to True
    If the case was not, check that it has audit activity less than settings.RECENTLY_UPDATED_WORKING_DAYS
    ago and return True, else return False
    """
    now = timezone.now()
    recent_audits = (
        Audit.objects.filter(
            target_content_type=ContentType.objects.get_for_model(Case),
            target_object_id__in=[
                case["id"]
                for case in cases
                if working_days_in_range(case["submitted_at"], now) > settings.RECENTLY_UPDATED_WORKING_DAYS
            ],
            actor_content_type=ContentType.objects.get_for_model(GovUser),
            created_at__gt=now - timedelta(days=number_of_days_since(now, settings.RECENTLY_UPDATED_WORKING_DAYS)),
        )
        .values("target_object_id")
        .annotate(Count("target_object_id"))
    )

    audit_dict = {audit["target_object_id"]: audit["target_object_id__count"] for audit in recent_audits}

    for case in cases:
        case["is_recently_updated"] = bool(
            working_days_in_range(case["submitted_at"], now) < settings.RECENTLY_UPDATED_WORKING_DAYS
            or audit_dict.get(case["id"])
        )


def get_hmrc_sla_hours(cases: List[Dict]):
    hmrc_cases = [case["id"] for case in cases if case["case_type"]["sub_type"]["key"] == CaseTypeSubTypeEnum.HMRC]
    hmrc_cases_goods_not_left_country = [
        str(id)
        for id in HmrcQuery.objects.filter(id__in=hmrc_cases, have_goods_departed=False).values_list("id", flat=True)
    ]

    for case in cases:
        if case["id"] in hmrc_cases_goods_not_left_country:
            case["sla_hours_since_raised"] = working_hours_in_range(case["submitted_at"], timezone.now())
