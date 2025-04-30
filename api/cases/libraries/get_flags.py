from django.db.models import Q, QuerySet, When, Case as DB_Case, IntegerField, BinaryField

from api.cases.models import Case
from api.flags.enums import FlagLevels
from api.flags.models import Flag
from api.flags.serializers import CaseListFlagSerializer
from api.teams.models import Team


def get_goods_flags(case):
    return Flag.objects.filter(goods__goods_on_application__application_id=case.id)


def get_destination_flags(case):
    # Usually destination level flags are attached to `Party` but some of the flags
    # are attached to `PartyOnApplication` so gather all of them
    flags = Flag.objects.filter(
        (
            Q(parties__parties_on_application__application_id=case.id)
            & Q(parties__parties_on_application__deleted_at__isnull=True)
        )
        | (Q(parties_on_application__application__pk=case.id) & Q(parties_on_application__deleted_at__isnull=True))
    )
    return flags


def get_flags(case: Case) -> QuerySet:
    """
    Get all case flags in no particular order
    """
    goods_flags = get_goods_flags(case)
    destination_flags = get_destination_flags(case)
    case_flags = case.flags.all()
    # Prefetch the organisation flag IDs to avoid generating SLOW queries elsewhere
    # (e.g. get_ordered_flags which uses this result)
    org_flag_ids = case.organisation.flags.values_list("id", flat=True)
    org_flags = Flag.objects.filter(id__in=org_flag_ids)

    return goods_flags | destination_flags | case_flags | org_flags


def get_ordered_flags(case: Case, team: Team, limit: int = None, distinct: bool = False):
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

    if distinct:
        all_flags = all_flags.distinct()

    if limit:
        all_flags = all_flags[:limit]

    return CaseListFlagSerializer(all_flags, many=True).data
