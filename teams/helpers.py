from conf.exceptions import NotFoundError
from teams.models import Team


def get_team_by_pk(pk):
    try:
        return Team.objects.get(pk=pk)
    except Team.DoesNotExist:
        raise NotFoundError({"team": "Team not found - " + str(pk)})


def get_admin_team():
    return Team.objects.get(pk="00000000-0000-0000-0000-000000000001")
