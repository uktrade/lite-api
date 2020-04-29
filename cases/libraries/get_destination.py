from django.db import models
from django.http import Http404

from applications.models import GoodOnApplication, CountryOnApplication
from cases.enums import CaseTypeSubTypeEnum
from cases.models import Case
from flags.models import Flag
from flags.serializers import CaseListFlagSerializer
from goodstype.models import GoodsType
from parties.models import Party
from queries.end_user_advisories.libraries.get_end_user_advisory import get_end_user_advisory_by_pk
from queries.goods_query.models import GoodsQuery
from static.countries.models import Country
from teams.models import Team


def get_destination(pk):
    try:
        destination = Country.objects.get(pk=pk)
    except Country.DoesNotExist:
        try:
            destination = Party.objects.get(pk=pk)
        except Party.DoesNotExist:
            raise Http404
    return destination


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
            .prefetch_related("good__flags")
            .values_list("good__flags", flat=True)
        )
    elif case_type in [
        CaseTypeSubTypeEnum.OPEN,
        CaseTypeSubTypeEnum.HMRC,
    ]:
        ids = GoodsType.objects.filter(application_id=case.id).select_related("flags").values_list("flags", flat=True)
    elif case_type == CaseTypeSubTypeEnum.GOODS:
        return GoodsQuery.objects.select_related("good").get(id=case.id).good.flags.all()

    return Flag.objects.filter(id__in=ids)


def get_destination_flags(case, case_type):
    ids = []

    if case_type == CaseTypeSubTypeEnum.EUA:
        return get_end_user_advisory_by_pk(case.id).end_user.flags.all()
    elif case_type == CaseTypeSubTypeEnum.OPEN:
        ids = (
            CountryOnApplication.objects.filter(application=case)
            .prefetch_related("country__flags")
            .values_list("country__flags", flat=True)
        )
    elif case_type == CaseTypeSubTypeEnum.STANDARD:
        ids = (
            case.baseapplication.parties.filter(deleted_at__isnull=True, party__flags__isnull=False)
            .prefetch_related("party__flags")
            .values_list("party__flags", flat=True)
        )

    return Flag.objects.filter(id__in=ids)


def annotate_my_team_flags(flags, priority, team):
    return flags.annotate(
        my_team=models.Case(
            models.When(team=team, then=models.Value(True)),
            default=models.Value(False),
            output_field=models.BooleanField(),
        )
    ).annotate(type=models.Value(priority, models.IntegerField()))


def get_flags(case: Case):
    """
    Get all case flags in no particular order (order will be specified by calling function)
    """
    case_type = case.case_type.sub_type

    goods_flags = get_goods_flags(case, case_type)
    destination_flags = get_destination_flags(case, case_type)
    case_flags = case.flags.all()
    org_flags = case.organisation.flags.all()

    return goods_flags.union(destination_flags).union(case_flags).union(org_flags)


def get_ordered_flags(case: Case, team: Team):
    case_type = case.case_type.sub_type

    goods_flags = annotate_my_team_flags(get_goods_flags(case, case_type), 0, team)
    destination_flags = annotate_my_team_flags(get_destination_flags(case, case_type), 1, team)
    case_flags = annotate_my_team_flags(case.flags.all(), 2, team)
    org_flags = annotate_my_team_flags(case.organisation.flags.all(), 3, team)

    all_flags = goods_flags.union(destination_flags).union(case_flags).union(org_flags)
    all_flags = all_flags.order_by("-my_team", "type", "priority")

    return CaseListFlagSerializer(all_flags, many=True).data


def sort_flags_by_team_and_priority(flag_data, team):
    flag_data = sorted(flag_data, key=lambda x: x["priority"])

    if not team:
        return flag_data

    # Group flags by user's team.
    team_flags, non_team_flags = [], []
    for flag in flag_data:
        team_flags.append(flag) if flag["team"] == team.id else non_team_flags.append(flag)

    return team_flags, non_team_flags
