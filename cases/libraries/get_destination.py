from django.db.models import Prefetch
from django.http import Http404

from applications.libraries.get_applications import get_application
from applications.models import GoodOnApplication, CountryOnApplication, StandardApplication
from cases.enums import CaseTypeSubTypeEnum, CaseTypeTypeEnum
from cases.models import Case
from flags.serializers import CaseListFlagSerializer
from goodstype.models import GoodsType
from parties.enums import PartyType
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


def get_standard_application_destination_flags(application):
    party_on_applications = application.active_parties.prefetch_related("party__flags").filter(
        deleted_at__isnull=True, party__flags__isnull=False
    )
    flags = []
    for poa in party_on_applications:
        flags += poa.party.flags.all()
        if poa.party.type in [PartyType.THIRD_PARTY, PartyType.ULTIMATE_END_USER]:
            flags += get_destination(poa.party.id).flags.all()

    return flags


def get_destination_flags(case):
    flags = []

    countries_on_application = CountryOnApplication.objects.filter(application=case).select_related("country")
    for country_on_application in countries_on_application:
        flags += country_on_application.country.flags.all()

    if case.case_type.sub_type == CaseTypeSubTypeEnum.EUA:
        query = get_end_user_advisory_by_pk(case.id)
        if query.end_user:
            flags += query.end_user.flags.all()
    elif case.case_type == CaseTypeTypeEnum.APPLICATION:
        application = get_application(case.id)
        if isinstance(application, StandardApplication):
            flags += get_standard_application_destination_flags(application)

    return flags


def get_goods_flags(case):
    goods_flags = []
    case_type = case.case_type.sub_type

    if case_type in [
        CaseTypeSubTypeEnum.STANDARD,
        CaseTypeSubTypeEnum.EUA,
        CaseTypeSubTypeEnum.EXHIBITION,
        CaseTypeSubTypeEnum.GIFTING,
        CaseTypeSubTypeEnum.F680,
    ]:
        goods_on_application = GoodOnApplication.objects.select_related("good").filter(application_id=case.id)
        for good_on_application in goods_on_application:
            goods_flags += good_on_application.good.flags.all()
    elif case_type in [
        CaseTypeSubTypeEnum.OPEN,
        CaseTypeSubTypeEnum.HMRC,
    ]:
        goods_types = GoodsType.objects.filter(application_id=case.id)
        for goods_type in goods_types:
            goods_flags += goods_type.flags.all()
    elif case_type == CaseTypeSubTypeEnum.GOODS:
        goods_flags += GoodsQuery.objects.select_related("good").get(id=case.id).good.flags.all()

    return goods_flags


def get_ordered_flags(case: Case, team: Team):
    case_flags = case.flags.all()
    org_flags = case.organisation.flags.all()
    goods_flags = get_goods_flags(case)
    destination_flags = get_destination_flags(case)

    flag_data = (
        sort_flags_by_team_and_name(CaseListFlagSerializer(set(goods_flags), many=True).data, team)
        + sort_flags_by_team_and_name(CaseListFlagSerializer(set(destination_flags), many=True).data, team)
        + sort_flags_by_team_and_name(CaseListFlagSerializer(case_flags, many=True).data, team)
        + sort_flags_by_team_and_name(CaseListFlagSerializer(org_flags, many=True).data, team)
    )
    return flag_data


def sort_flags_by_team_and_name(flag_data, team):
    flag_data = sorted(flag_data, key=lambda x: x["name"])

    if not team:
        return flag_data

    # Group flags by user's team.
    team_flags, non_team_flags = [], []
    for flag in flag_data:
        team_flags.append(flag) if flag["team"] == str(team.id) else non_team_flags.append(flag)

    return team_flags + non_team_flags
