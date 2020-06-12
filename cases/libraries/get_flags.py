from django.db.models import QuerySet, When, Case as DB_Case, IntegerField, BinaryField

from applications.models import CountryOnApplication
from cases.enums import CaseTypeSubTypeEnum
from cases.models import Case
from flags.enums import FlagLevels
from flags.models import Flag
from flags.serializers import CaseListFlagSerializer
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
        return Flag.objects.filter(goods__goods_on_application__application_id=case.id)
        # ids = GoodOnApplication.objects.filter(application_id=case.id).values_list("good__flags", flat=True)
    elif case_type in [
        CaseTypeSubTypeEnum.OPEN,
        CaseTypeSubTypeEnum.HMRC,
    ]:
        return Flag.objects.filter(goods_type__application_id=case.id)
        # ids = GoodsType.objects.filter(application_id=case.id).values_list("flags", flat=True)
    elif case_type == CaseTypeSubTypeEnum.GOODS:
        return GoodsQuery.objects.select_related("good").get(id=case.id).good.flags.all()

    return Flag.objects.filter(id__in=ids).select_related("team")


def get_destination_flags(case, case_type):
    ids = []

    if case_type == CaseTypeSubTypeEnum.EUA:
        return get_end_user_advisory_by_pk(case.id).end_user.flags.all()
    elif case_type == CaseTypeSubTypeEnum.OPEN:
        ids = set(
            CountryOnApplication.objects.filter(application=case)
            .prefetch_related("country__flags")
            .values_list("country__flags", flat=True)
        )

        ids = ids | set(CountryOnApplication.objects.filter(application=case).values_list("flags", flat=True))

    elif case_type == CaseTypeSubTypeEnum.STANDARD:
        ids = case.baseapplication.parties.filter(deleted_at__isnull=True, party__flags__isnull=False).values_list(
            "party__flags", flat=True
        )

    return Flag.objects.filter(id__in=ids).select_related("team")


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


def get_ordered_flags(case: Case, team: Team, limit: int = None):
    case_type = case.case_type.sub_type

    goods_flags = get_goods_flags(case, case_type)
    destination_flags = get_destination_flags(case, case_type)
    case_flags = case.flags.all()
    organisation_flags = case.organisation.flags.all()

    all_flags = goods_flags | destination_flags | case_flags | organisation_flags

    all_flags = all_flags.annotate(
        my_team=DB_Case(When(team_id=team.id, then=True), default=False, output_field=BinaryField()),
        order=DB_Case(
            When(level=FlagLevels.GOOD, then=0),
            When(level=FlagLevels.DESTINATION, then=1),
            When(level=FlagLevels.CASE, then=2),
            default=3,
            output_field=IntegerField(),
        ),
    ).order_by("-my_team", "order", "priority")

    if limit:
        all_flags = all_flags[:limit]

    return CaseListFlagSerializer(all_flags, many=True).data
