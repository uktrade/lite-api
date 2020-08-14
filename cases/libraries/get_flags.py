from django.db.models import QuerySet, When, Case as DB_Case, IntegerField, BinaryField

from cases.enums import CaseTypeSubTypeEnum
from cases.models import Case
from flags.enums import FlagLevels
from flags.models import Flag
from flags.serializers import CaseListFlagSerializer
from api.teams.models import Team


def get_goods_flags(case, case_type):
    if case_type in [
        CaseTypeSubTypeEnum.STANDARD,
        CaseTypeSubTypeEnum.EUA,
        CaseTypeSubTypeEnum.EXHIBITION,
        CaseTypeSubTypeEnum.GIFTING,
        CaseTypeSubTypeEnum.F680,
    ]:
        return Flag.objects.filter(goods__goods_on_application__application_id=case.id)
    elif case_type in [
        CaseTypeSubTypeEnum.OPEN,
        CaseTypeSubTypeEnum.HMRC,
    ]:
        return Flag.objects.filter(goods_type__application_id=case.id)
    elif case_type == CaseTypeSubTypeEnum.GOODS:
        return Flag.objects.filter(goods__good__id=case.id)

    return Flag.objects.none()


def get_destination_flags(case, case_type):
    if case_type == CaseTypeSubTypeEnum.EUA:
        return Flag.objects.filter(parties__parties_on_application__application_id=case.id)
    elif case_type == CaseTypeSubTypeEnum.OPEN:
        return Flag.objects.filter(countries_on_applications__application_id=case.id) | Flag.objects.filter(
            countries__countries_on_application__application_id=case.id
        )

    elif case_type == CaseTypeSubTypeEnum.STANDARD:
        return Flag.objects.filter(
            parties__parties_on_application__application_id=case.id,
            parties__parties_on_application__deleted_at__isnull=True,
        )

    return Flag.objects.none()


def get_flags(case: Case) -> QuerySet:
    """
    Get all case flags in no particular order
    """
    # Ensure that case_type is prefetched, or an additional query will be made for each case.
    case_type = case.case_type.sub_type

    goods_flags = get_goods_flags(case, case_type)
    destination_flags = get_destination_flags(case, case_type)
    case_flags = case.flags.all()
    org_flags = Flag.objects.filter(organisations__cases__id=case.id)

    return goods_flags | destination_flags | case_flags | org_flags


def get_ordered_flags(case: Case, team: Team, limit: int = None):
    """
    This function will get the flags for cases looking at good, destination, case, and organisation flags. The flags
        will be ordered with your teams flags first, in order of category (same order as above), and priority
        (lowest first).

    :param case: case object the flags relate to
    :param team: The team for user making the request
    :param limit: If assigned will return no more than given amount
    :return: List of flags serialized
    """
    all_flags = get_flags(case)

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
