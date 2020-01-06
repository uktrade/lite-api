from django.http import Http404

from applications.libraries.get_applications import get_application
from applications.models import GoodOnApplication, CountryOnApplication, StandardApplication
from cases.enums import CaseTypeEnum
from cases.models import Case
from flags.serializers import FlagSerializer
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
    flags = []
    flags += application.end_user.flags.all()
    flags += application.consignee.flags.all()

    for ultimate_end_user in application.ultimate_end_users.values_list("id", flat=True):
        flags += get_destination(ultimate_end_user).flags.all()

    for third_party in application.third_parties.values_list("id", flat=True):
        flags += get_destination(third_party).flags.all()

    return flags


def get_destination_flags(case):
    flags = []

    countries_on_application = CountryOnApplication.objects.filter(application=case).select_related("country")
    for country_on_application in countries_on_application:
        flags += country_on_application.country.flags.all()

    if case.type == CaseTypeEnum.END_USER_ADVISORY_QUERY:
        query = get_end_user_advisory_by_pk(case.id)
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
        goods = GoodOnApplication.objects.filter(application=case).select_related("good")
        for good in goods:
            goods_flags += good.good.flags.all()
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
