from datetime import timedelta
from typing import List, Dict

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Case as DjangoCase
from django.db.models import Count, F, Q, When, UUIDField
from django.db.models import Value
from django.db.models.functions import Concat
from django.utils import timezone

from api.applications.models import HmrcQuery
from api.audit_trail.models import Audit
from cases.enums import CaseTypeEnum, CaseTypeSubTypeEnum, AdviceType
from cases.models import Case
from api.common.dates import working_days_in_range, number_of_days_since, working_hours_in_range
from api.flags.serializers import CaseListFlagSerializer
from api.organisations.models import Organisation
from api.static.statuses.enums import CaseStatusEnum
from api.users.enums import UserStatuses
from api.users.models import GovUser


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


def populate_other_flags(cases: List[Dict]):
    from api.flags.models import Flag

    case_ids = [case["id"] for case in cases]

    case_flags = Flag.objects.filter(cases__id__in=case_ids).annotate(case_id=F("cases__id"))
    organisation_flags = Flag.objects.filter(organisations__cases__id__in=case_ids).annotate(
        case_id=F("organisations__cases__id")
    )
    union_flags = [*case_flags, *organisation_flags]

    for case in cases:
        case["flags"] = CaseListFlagSerializer(
            {flag for flag in union_flags if str(flag.case_id) == str(case["id"])}, many=True
        ).data

    return cases


def populate_goods_flags(cases: List[Dict]):
    from api.flags.models import Flag

    case_ids = [case["id"] for case in cases]
    flags = Flag.objects.filter(
        Q(goods__goods_on_application__application_id__in=case_ids)
        | Q(goods_type__application_id__in=case_ids)
        | Q(goods__good__id__in=case_ids)
    ).annotate(
        case_id=DjangoCase(
            When(
                goods__goods_on_application__application_id__in=case_ids,
                then=F("goods__goods_on_application__application_id"),
            ),
            When(goods_type__application_id__in=case_ids, then=F("goods_type__application_id")),
            When(goods__good__id__in=case_ids, then=F("goods__good__id")),
            default=None,
            output_field=UUIDField(),
        )
    )

    for case in cases:
        case["goods_flags"] = CaseListFlagSerializer(
            {flag for flag in flags if str(flag.case_id) == str(case["id"])}, many=True
        ).data

    return cases


def populate_destinations_flags(cases: List[Dict]):
    from api.flags.models import Flag

    case_ids = [case["id"] for case in cases]
    flags = Flag.objects.filter(
        Q(parties__parties_on_application__application_id__in=case_ids)
        | Q(
            parties__parties_on_application__application_id__in=case_ids,
            parties__parties_on_application__deleted_at__isnull=True,
        )
        | Q(countries_on_applications__application_id__in=case_ids)
        | Q(countries__countries_on_application__application_id__in=case_ids)
    ).annotate(
        case_id=DjangoCase(
            When(
                parties__parties_on_application__application_id__in=case_ids,
                then=F("parties__parties_on_application__application_id"),
            ),
            When(
                parties__parties_on_application__application_id__in=case_ids,
                then=F("parties__parties_on_application__application_id"),
            ),
            When(
                countries_on_applications__application_id__in=case_ids,
                then=F("countries_on_applications__application_id"),
            ),
            When(
                countries__countries_on_application__application_id__in=case_ids,
                then=F("countries__countries_on_application__application_id"),
            ),
            default=None,
            output_field=UUIDField(),
        )
    )

    for case in cases:
        case["destinations_flags"] = CaseListFlagSerializer(
            {flag for flag in flags if str(flag.case_id) == str(case["id"])}, many=True
        ).data

    return cases


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

    return cases


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
