from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from teams.libraries.get_team import get_team_by_pk
from teams.models import Team
from teams.serializers import TeamSerializer


class TeamList(APIView):
    """
    List all teams, or create a new team.
    """
    def get(self, request):
        teams = Team.objects.all().order_by('name')
        serializer = TeamSerializer(teams, many=True)
        return JsonResponse(data={'teams': serializer.data})

    def post(self, request):
        data = JSONParser().parse(request)
        serializer = TeamSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'team': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class TeamDetail(APIView):

    def get_object(self, pk):
        return get_team_by_pk(pk)

    def get(self, request, pk):
        team = get_team_by_pk(pk)

        serializer = TeamSerializer(team)
        return JsonResponse(data={'team': serializer.data})

    def put(self, request, pk):
        data = JSONParser().parse(request)
        serializer = TeamSerializer(self.get_object(pk), data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'team': serializer.data})
        return JsonResponse(data={'errors': serializer.errors},
                            status=400)
