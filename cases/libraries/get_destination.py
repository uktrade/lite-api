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


def get_destination_flags(instance):
    application = get_application(instance.id)
    countries = CountryOnApplication.objects.filter(application=instance).select_related("country")
    countries_flags = list(itertools.chain.from_iterable([c.country.flags.order_by("name") for c in countries]))
    country_flag_data = FlagSerializer(countries_flags, many=True).data
    flag_data = country_flag_data
    if isinstance(application, StandardApplication):
        end_user_flags = [flag for flag in application.end_user.flags.order_by("name")]
        end_user_flag_data = FlagSerializer(end_user_flags, many=True).data
        flag_data += end_user_flag_data
        consignee_flags = [flag for flag in application.consignee.flags.order_by("name") if flag not in end_user_flags]
        consignee_flag_data = FlagSerializer(consignee_flags, many=True).data
        flag_data += consignee_flag_data
        ultimate_end_users = [
            ultimate_end_user_id for ultimate_end_user_id in application.ultimate_end_users.values_list("id", flat=True)
        ]
        ultimate_end_users_flags = []
        for ultimate_end_user in ultimate_end_users:
            [
                ultimate_end_users_flags.append(flag)
                for flag in get_destination(str(ultimate_end_user)).flags.order_by("name")
                if flag not in (ultimate_end_users_flags or end_user_flags or consignee_flags)
            ]
        ultimate_end_user_flag_data = FlagSerializer(ultimate_end_users_flags, many=True).data
        flag_data += ultimate_end_user_flag_data
        third_parties = [third_party_id for third_party_id in application.third_parties.values_list("id", flat=True)]
        third_parties_flags = []
        for third_party in third_parties:
            [
                third_parties_flags.append(flag)
                for flag in get_destination(third_party).flags.order_by("name")
                if flag not in (third_parties_flags or ultimate_end_users_flags or end_user_flags or consignee_flags)
            ]
        third_party_flag_data = FlagSerializer(third_parties_flags, many=True).data
        flag_data += third_party_flag_data

    return flag_data


def get_ordered_flags(instance, team):
    case_flag_data = FlagSerializer(instance.flags.order_by("name"), many=True).data
    org_flag_data = FlagSerializer(instance.organisation.flags.order_by("name"), many=True).data

    if instance.type in [CaseTypeEnum.APPLICATION, CaseTypeEnum.HMRC_QUERY]:
        goods = GoodOnApplication.objects.filter(application=instance).select_related("good")
        goods_flags = list(itertools.chain.from_iterable([g.good.flags.order_by("name") for g in goods]))
        good_ids = {}
        goods_flags = [good_ids.setdefault(g, g) for g in goods_flags if g.id not in good_ids]  # dedup
        good_flag_data = FlagSerializer(goods_flags, many=True).data
        destination_flag_data = get_destination_flags(instance)
    else:
        good_flag_data = []
        destination_flag_data = []

    flag_data = case_flag_data + org_flag_data + good_flag_data + destination_flag_data
    flag_data = sorted(flag_data, key=lambda x: x["name"])

    if not team:
        return flag_data

    # Sort flags by user's team.
    team_flags, non_team_flags = [], []
    for flag in flag_data:
        team_flags.append(flag) if flag["team"]["id"] == str(team.id) else non_team_flags.append(flag)

    return team_flags + non_team_flags
