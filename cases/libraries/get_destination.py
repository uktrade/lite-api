import itertools

from applications.libraries.get_applications import get_application
from applications.models import GoodOnApplication, CountryOnApplication, StandardApplication
from cases.enums import CaseTypeEnum
from flags.serializers import FlagSerializer
from parties.models import Party
from static.countries.models import Country


def get_destination(pk):
    try:
        destination = Country.objects.get(pk=pk)
    except Country.DoesNotExist:
        destination = Party.objects.get(pk=pk)
    return destination


def get_standard_application_destination_flags(application, flags):
    [flags.append(flag) for flag in application.end_user.flags.order_by("name") if flag not in flags]
    [flags.append(flag) for flag in application.consignee.flags.order_by("name") if flag not in flags]
    ultimate_end_users = [
        ultimate_end_user_id for ultimate_end_user_id in application.ultimate_end_users.values_list("id", flat=True)
    ]
    for ultimate_end_user in ultimate_end_users:
        [
            flags.append(flag)
            for flag in get_destination(str(ultimate_end_user)).flags.order_by("name")
            if flag not in flags
        ]
    third_parties = [third_party_id for third_party_id in application.third_parties.values_list("id", flat=True)]
    for third_party in third_parties:
        [flags.append(flag) for flag in get_destination(third_party).flags.order_by("name") if flag not in flags]
    return flags


def get_destination_flags(instance):
    application = get_application(instance.id)
    countries = CountryOnApplication.objects.filter(application=instance).select_related("country")
    countries_flags = list(itertools.chain.from_iterable([c.country.flags.order_by("name") for c in countries]))
    flags = countries_flags
    if isinstance(application, StandardApplication):
        standard_application_destination_flags = get_standard_application_destination_flags(application, flags)
        flags += standard_application_destination_flags

    return flags


def get_ordered_flags(instance, team):
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
        + FlagSerializer(goods_flags, many=True).data
        + FlagSerializer(destination_flags, many=True).data
    )
    flag_data = sorted(flag_data, key=lambda x: x["name"])

    if not team:
        return flag_data

    # Sort flags by user's team.
    team_flags, non_team_flags = [], []
    for flag in flag_data:
        team_flags.append(flag) if flag["team"]["id"] == str(team.id) else non_team_flags.append(flag)

    return team_flags + non_team_flags
