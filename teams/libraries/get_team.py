from django.http import Http404

from teams.models import Team


def get_team_by_pk(pk):
    try:
        return Team.objects.get(pk=pk)
    except Team.DoesNotExist:
        raise Http404