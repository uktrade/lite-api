from api.teams import models as team_models
from api.teams import serializers as team_serializers


def get_teams():
    return team_serializers.TeamSerializer(team_models.Team.objects.all(), many=True).data


def get_team_query_options():
    all_teams = [team for team in get_teams() if team["name"] != "Admin"]
    ogd_teams = [t["name"] for t in all_teams if not t["part_of_ecju"]]

    as_field = lambda s: f'{s.replace("-", "_").replace(" ", "_")}_days'.lower()

    ogd_team_options = [{"name": name, "field_name": as_field(name)} for name in ogd_teams]

    query_items = []
    select_items = []

    ogd_teams_str = ",".join([f'team_sla_days_agg.{item["field_name"]}' for item in ogd_team_options])
    select_items.append(
        f'(select greatest({ogd_teams_str}) where team_sla_days_agg.case_id = applications.case_id)    "REVIEW_DAYS"'
    )
    select_items.append(
        f'(select applications.sla_days - greatest({ogd_teams_str}) where team_sla_days_agg.case_id = applications.case_id)    "DIT_DAYS"'
    )

    # DIT days are calculated separately
    for team in ogd_team_options:
        team_name = team["name"]
        field_name = team["field_name"]
        query_items.append(
            f"coalesce(sum(sum_sla_days) filter ( where team_name = '{team_name}' ), 0) \"{field_name}\""
        )

        # select statements to extract required fields from the table
        select_items.append(f'team_sla_days_agg.{field_name}    "{field_name.upper()}"')

    return {"team_filter_string": ",".join(query_items), "team_select_string": ",".join(select_items)}
