import itertools

from django.http import Http404

from applications.libraries.get_applications import get_application
from applications.models import GoodOnApplication, CountryOnApplication, StandardApplication
from cases.enums import CaseTypeEnum
from cases.models import Case
from flags.serializers import FlagSerializer
from parties.models import Party
from static.countries.models import Country
from teams.models import Team


class DestinationNotFoundError(Exception):
    def __init__(self):
        raise Http404


def get_destination(pk):
    try:
        destination = Country.objects.get(pk=pk)
    except Country.DoesNotExist:
        try:
            destination = Party.objects.get(pk=pk)
        except Party.DoesNotExist:
            raise DestinationNotFoundError
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


def get_destination_flags(instance):
    application = get_application(instance.id)
    countries = CountryOnApplication.objects.filter(application=instance).select_related("country")
    flags = [country.country.flags.all() for country in countries.values_list("id", flat=True)]
    if isinstance(application, StandardApplication):
        flags += get_standard_application_destination_flags(application)

    return flags


def get_ordered_flags(instance: Case, team: Team):
    case_flags = instance.flags.order_by("name")
    org_flags = instance.organisation.flags.order_by("name")

    if instance.type in [CaseTypeEnum.APPLICATION, CaseTypeEnum.HMRC_QUERY]:
        goods = GoodOnApplication.objects.filter(application=instance).select_related("good")
        goods_flags = list(itertools.chain.from_iterable([g.good.flags.order_by("name") for g in goods]))
        good_ids = {}
        goods_flags = [good_ids.setdefault(g, g) for g in goods_flags if g.id not in good_ids]  # dedup
        destination_flags = get_destination_flags(instance)
    else:
        goods_flags = []
        destination_flags = []

    flag_data = (
        FlagSerializer(case_flags, many=True).data
        + FlagSerializer(org_flags, many=True).data
        + FlagSerializer(set(goods_flags), many=True).data
        + FlagSerializer(set(destination_flags), many=True).data
    )
    flag_data = sorted(flag_data, key=lambda x: x["name"])

    if not team:
        return flag_data

    # Group flags by user's team.
    team_flags, non_team_flags = [], []
    for flag in flag_data:
        team_flags.append(flag) if flag["team"]["id"] == str(team.id) else non_team_flags.append(flag)

    return team_flags + non_team_flags
