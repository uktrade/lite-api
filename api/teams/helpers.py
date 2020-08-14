from api.conf.exceptions import NotFoundError
from api.teams.models import Team


def get_team_by_pk(pk):
    try:
        return Team.objects.get(pk=pk)
    except Team.DoesNotExist:
        raise NotFoundError({"team": "Team not found - " + str(pk)})
