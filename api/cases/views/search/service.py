from datetime import timedelta
from typing import List, Dict
from collections import defaultdict

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, F, Value
from django.db.models.functions import Concat
from django.utils import timezone
from api.audit_trail.service import serialize_case_activity
from api.staticdata.countries.serializers import CountrySerializer

from api.applications.models import HmrcQuery, PartyOnApplication, GoodOnApplication, DenialMatchOnApplication
from api.audit_trail.models import Audit
from api.cases.enums import CaseTypeEnum, CaseTypeSubTypeEnum, AdviceType
from api.cases import serializers as cases_serializers
from api.applications.serializers.advice import AdviceSearchViewSerializer
from api.cases.models import Case, EcjuQuery, Advice
from api.common.dates import working_days_in_range, number_of_days_since, working_hours_in_range
from api.flags.serializers import CaseListFlagSerializer
from api.organisations.models import Organisation
from api.staticdata.statuses.enums import CaseStatusEnum
from api.users.enums import UserStatuses
from api.users.models import BaseUser, GovUser


def get_case_status_list() -> List[Dict]:
    return CaseStatusEnum.as_list()


def get_case_type_type_list() -> List[Dict]:
    return CaseTypeEnum.case_types_to_representation()


def get_gov_users_list():
    return (
        GovUser.objects.filter(status=UserStatuses.ACTIVE)
        .annotate(
            full_name=Concat("baseuser_ptr__first_name", Value(" "), "baseuser_ptr__last_name"),
        )
        .values("full_name", pending=F("baseuser_ptr__pending"), id=F("baseuser_ptr_id"))
    )


def get_advice_types_list():
    return AdviceType.to_representation()


def populate_other_flags(cases: List[Dict]):
    from api.flags.models import Flag

    case_ids = [case["id"] for case in cases]

    union_flags = set(
        [
            *Flag.objects.filter(cases__id__in=case_ids).annotate(case_id=F("cases__id")),
            *Flag.objects.filter(organisations__cases__id__in=case_ids).annotate(case_id=F("organisations__cases__id")),
        ]
    )

    for case in cases:
        case_id = str(case["id"])
        flags = [flag for flag in union_flags if str(flag.case_id) == case_id]
        case["flags"] = CaseListFlagSerializer(flags, many=True).data


def populate_goods_flags(cases: List[Dict]):
    from api.flags.models import Flag

    case_ids = [case["id"] for case in cases]
    qs1 = Flag.objects.filter(goods__goods_on_application__application_id__in=case_ids).annotate(
        case_id=F("goods__goods_on_application__application_id"),
    )
    qs2 = Flag.objects.filter(goods_type__application_id__in=case_ids).annotate(
        case_id=F("goods_type__application_id"),
    )
    qs3 = Flag.objects.filter(goods__good__id__in=case_ids).annotate(
        case_id=F("goods__good__id"),
    )
    flags = qs1.union(qs2, qs3)

    for case in cases:
        case["goods_flags"] = CaseListFlagSerializer(
            {flag for flag in flags if str(flag.case_id) == str(case["id"])}, many=True
        ).data


def populate_destinations_flags(cases: List[Dict]):
    from api.flags.models import Flag

    case_ids = [case["id"] for case in cases]

    flags = Flag.objects.filter(parties__parties_on_application__application_id__in=case_ids).annotate(
        case_id=F("parties__parties_on_application__application_id")
    )
    flags = flags.union(
        Flag.objects.filter(
            parties__parties_on_application__application_id__in=case_ids,
            parties__parties_on_application__deleted_at__isnull=True,
        ).annotate(case_id=F("parties__parties_on_application__application_id"))
    )
    flags = flags.union(
        Flag.objects.filter(countries_on_applications__application_id__in=case_ids).annotate(
            case_id=F("countries_on_applications__application_id")
        )
    )
    flags = flags.union(
        Flag.objects.filter(countries__countries_on_application__application_id__in=case_ids).annotate(
            case_id=F("countries__countries_on_application__application_id")
        )
    )
    flags = flags.union(
        Flag.objects.filter(parties_on_application__application__pk__in=case_ids).annotate(
            case_id=F("parties_on_application__application_id")
        )
    )

    for case in cases:
        # It would seem sensible here to do flags.filter(case_id=case["id"]) however one cannot do further filtering on
        # union queries
        case_flags = {flag for flag in flags if str(flag.case_id) == str(case["id"])}
        case["destinations_flags"] = CaseListFlagSerializer(case_flags, many=True).data


def populate_organisation(cases: List[Dict]):
    from api.organisations.serializers import OrganisationCaseSerializer

    case_ids = [case["id"] for case in cases]
    organisations = (
        Organisation.objects.filter(cases__id__in=case_ids)
        .annotate(case_id=F("cases__id"))
        .select_related("primary_site")
        .prefetch_related(
            "primary_site__address",
            "primary_site__address__country",
            "primary_site__site_records_located_at",
            "primary_site__site_records_located_at__address",
            "primary_site__site_records_located_at__address__country",
        )
    )

    for case in cases:
        organisation = next(
            organisation for organisation in organisations if str(organisation.case_id) == str(case["id"])
        )
        case["organisation"] = OrganisationCaseSerializer(organisation).data


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


def populate_destinations(case_map):
    poas = PartyOnApplication.objects.select_related("party", "party__country").filter(
        application__in=list(case_map.keys()), deleted_at=None
    )
    for poa in poas:
        serializer = CountrySerializer(poa.party.country)
        data = serializer.data
        case = case_map[str(poa.application_id)]
        case["destinations"].append({"country": data})


def populate_good_details(case_map):
    goas = (
        GoodOnApplication.objects.select_related(
            "report_summary_subject",
            "report_summary_prefix",
            "good",
        )
        .prefetch_related(
            "control_list_entries",
            "regime_entries",
        )
        .filter(application__in=list(case_map.keys()))
    )
    for goa in goas:
        case = case_map[str(goa.application_id)]
        serializer = cases_serializers.GoodOnApplicationSummarySerializer(goa)
        case["goods"].append(serializer.data)


def populate_denials(case_map):
    doas = (
        DenialMatchOnApplication.objects.select_related(
            "denial",
        )
        .prefetch_related()
        .filter(application__in=list(case_map.keys()))
    )
    for doa in doas:
        case = case_map[str(doa.application_id)]
        serializer = cases_serializers.DenialMatchOnApplicationSummarySerializer(doa)
        case["denials"].append(serializer.data)


def populate_advice(case_map):
    case_advices = (
        Advice.objects.select_related("user", "user__team", "user__role", "user__baseuser_ptr")
        .prefetch_related("denial_reasons")
        .filter(case_id__in=list(case_map.keys()))
    )

    for case_advice in case_advices:
        case = case_map[str(case_advice.case_id)]
        case_advice_result = defaultdict(list)
        # Filter duplicate advice records, which is duplicated per good
        advice_key = f"{case_advice.user.team.id}-{case_advice.type}"
        if not case_advice_result[advice_key]:
            serializer = AdviceSearchViewSerializer(case_advice)
            case_advice_result[advice_key].append(serializer.data)
        case["advice"] = case_advice_result


def populate_ecju_queries(case_map):
    for case in case_map.values():
        case["ecju_queries"] = []

    queries = (
        EcjuQuery.objects.select_related(
            "raised_by_user",
            "responded_by_user",
            "raised_by_user__baseuser_ptr",
            "responded_by_user__baseuser_ptr",
        )
        .prefetch_related()
        .filter(case_id__in=list(case_map.keys()))
    )
    for query in queries:
        case = case_map[str(query.case_id)]
        serializer = cases_serializers.ECJUQuerySummarySerializer(query)
        case["ecju_queries"].append(serializer.data)


def populate_activity_updates(case_map):
    """
    retrieve the last 2 activities per case for the provided list of cases
    """
    case_ids = list(case_map.keys())
    activities_qs = Audit.objects.get_latest_activities(case_ids, 2)
    # get users data for activities en bulk to reduce query count
    user_ids = {activity.actor_object_id for activity in activities_qs}
    users = BaseUser.objects.select_related("exporteruser", "govuser", "govuser__team").filter(id__in=user_ids)
    user_map = {str(user.id): user for user in users}

    for activity in activities_qs:
        case_id = None
        # get case id from either of the audit record fields
        if activity.target_object_id in case_ids:
            case_id = activity.target_object_id
        else:
            case_id = activity.action_object_object_id
        # prepopulate actor for AuditSerializer
        actor = user_map[activity.actor_object_id]
        activity_obj = serialize_case_activity(activity, actor)
        case = case_map[case_id]
        if "activity_updates" in case:
            case["activity_updates"].append(activity_obj)
        else:
            case["activity_updates"] = [activity_obj]
    # filter down to 2 most recent records only
    for case in case_map.values():
        if "activity_updates" in case:
            case["activity_updates"] = sorted(case["activity_updates"], key=lambda d: d["created_at"], reverse=True)
            case["activity_updates"] = case["activity_updates"][:2]
