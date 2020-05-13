from django.db import models
from django.db.models import QuerySet

from applications.models import GoodOnApplication, CountryOnApplication
from cases.enums import CaseTypeSubTypeEnum
from cases.models import Case
from flags.models import Flag
from flags.serializers import CaseListFlagSerializer
from goodstype.models import GoodsType
from queries.end_user_advisories.libraries.get_end_user_advisory import get_end_user_advisory_by_pk
from queries.goods_query.models import GoodsQuery
from teams.models import Team


def get_goods_flags(case, case_type):
    ids = []

    if case_type in [
        CaseTypeSubTypeEnum.STANDARD,
        CaseTypeSubTypeEnum.EUA,
        CaseTypeSubTypeEnum.EXHIBITION,
        CaseTypeSubTypeEnum.GIFTING,
        CaseTypeSubTypeEnum.F680,
    ]:
        ids = (
            GoodOnApplication.objects.filter(application_id=case.id)
                .values_list("good__flags", flat=True)
        )
    elif case_type in [
        CaseTypeSubTypeEnum.OPEN,
        CaseTypeSubTypeEnum.HMRC,
    ]:
        ids = GoodsType.objects.filter(application_id=case.id).values_list("flags", flat=True)
    elif case_type == CaseTypeSubTypeEnum.GOODS:
        return GoodsQuery.objects.select_related("good").get(id=case.id).good.flags.all()

    return Flag.objects.filter(id__in=ids).select_related("team")


def get_destination_flags(case, case_type):
    ids = []

    if case_type == CaseTypeSubTypeEnum.EUA:
        return get_end_user_advisory_by_pk(case.id).end_user.flags.all()
    elif case_type == CaseTypeSubTypeEnum.OPEN:
        ids = (
            CountryOnApplication.objects.filter(application=case).values_list("country__flags", flat=True)
        )
    elif case_type == CaseTypeSubTypeEnum.STANDARD:
        ids = (
            case.baseapplication.parties.filter(deleted_at__isnull=True, party__flags__isnull=False).values_list("party__flags", flat=True)
        )

    return Flag.objects.filter(id__in=ids).select_related("team")


def annotate_my_team_flags(flags, priority, team):
    for flag in flags:
        flag.my_team = flag.team.id == team.id
        flag.priority = priority

    return flags


def get_flags(case: Case) -> QuerySet:
    """
    Get all case flags in no particular order (order will be specified by calling function)
    """
    case_type = case.case_type.sub_type

    goods_flags = get_goods_flags(case, case_type)
    destination_flags = get_destination_flags(case, case_type)
    case_flags = case.flags.all()
    org_flags = case.organisation.flags.all()

    return goods_flags | destination_flags | case_flags | org_flags


def get_ordered_flags(case: Case, team: Team):
    case_type = case.case_type.sub_type

    goods_flags = annotate_my_team_flags(get_goods_flags(case, case_type), 0, team)
    destination_flags = annotate_my_team_flags(get_destination_flags(case, case_type), 1, team)
    case_flags = annotate_my_team_flags(case.flags.all(), 2, team)
    organisation_flags = annotate_my_team_flags(case.organisation.flags.all(), 3, team)

    all_flags = [*goods_flags, *destination_flags, *case_flags, *organisation_flags]
    all_flags = sorted(all_flags, key=lambda x: (x.my_team, x.level, x.priority))

    return CaseListFlagSerializer(all_flags, many=True).data
