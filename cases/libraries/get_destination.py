from django.http import Http404

from applications.libraries.get_applications import get_application
from applications.models import GoodOnApplication, CountryOnApplication, StandardApplication
from cases.enums import CaseTypeEnum
from cases.models import Case
from flags.serializers import FlagSerializer
from goodstype.models import GoodsType
from parties.enums import PartyType
from parties.models import Party
from queries.end_user_advisories.libraries.get_end_user_advisory import get_end_user_advisory_by_pk
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

    if case.type == CaseTypeEnum.END_USER_ADVISORY_QUERY:
        query = get_end_user_advisory_by_pk(case.id)
        if query.end_user:
            flags += query.end_user.flags.all()
    else:
        application = get_application(case.id)
        if isinstance(application, StandardApplication):
            flags += get_standard_application_destination_flags(application)

    return flags


def get_ordered_flags(case: Case, team: Team):
    case_flags = case.flags.all()
    org_flags = case.organisation.flags.all()
    goods_flags = []
    destination_flags = []

    if case.type in [CaseTypeEnum.APPLICATION, CaseTypeEnum.HMRC_QUERY, CaseTypeEnum.END_USER_ADVISORY_QUERY]:
        goods_on_application = GoodOnApplication.objects.filter(application=case)
        if goods_on_application.exists():
            goods_on_application = goods_on_application.select_related("good")
            for good_on_application in goods_on_application:
                goods_flags += good_on_application.good.flags.all()
        else:
            goods_types = GoodsType.objects.filter(application=case)
            for goods_type in goods_types:
                goods_flags += goods_type.flags.all()

        destination_flags = get_destination_flags(case)

    flag_data = (
        sort_flags_by_team_and_name(FlagSerializer(set(goods_flags), many=True).data, team)
        + sort_flags_by_team_and_name(FlagSerializer(set(destination_flags), many=True).data, team)
        + sort_flags_by_team_and_name(FlagSerializer(case_flags, many=True).data, team)
        + sort_flags_by_team_and_name(FlagSerializer(org_flags, many=True).data, team)
    )
    return flag_data


def sort_flags_by_team_and_name(flag_data, team):
    flag_data = sorted(flag_data, key=lambda x: x["name"])

    if not team:
        return flag_data

    # Group flags by user's team.
    team_flags, non_team_flags = [], []
    for flag in flag_data:
        team_flags.append(flag) if flag["team"]["id"] == str(team.id) else non_team_flags.append(flag)

    return team_flags + non_team_flags
