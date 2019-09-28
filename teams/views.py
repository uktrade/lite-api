from django.http import JsonResponse
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import GovAuthentication
from conf.serializers import response_serializer
from gov_users.serializers import GovUserViewSerializer
from teams.helpers import get_team_by_pk
from teams.models import Team
from teams.serializers import TeamSerializer
from users.models import GovUser


class TeamList(APIView):
    """
    Gets a list of teams or add a new one
    """
    authentication_classes = (GovAuthentication,)

    @swagger_auto_schema(responses={
        200: openapi.Response('OK', TeamSerializer),
        })
    def get(self, request):
        """
        List all teams
        """
        teams = Team.objects.all().order_by('name')
        return response_serializer(TeamSerializer, obj=teams, many=True)

    @swagger_auto_schema(
        request_body=TeamSerializer,
        responses={
            400: 'JSON parse error'
        })
    def post(self, request):
        """
        Create a new team
        """
        data = JSONParser().parse(request)
        return response_serializer(TeamSerializer, data=data, object_class=Team)


class TeamDetail(APIView):
    """
    Perform action on a single team
    """
    authentication_classes = (GovAuthentication,)

    @swagger_auto_schema(responses={
        200: openapi.Response('OK', TeamSerializer),
    })
    def get(self, request, pk):
        """
        Retrieve a team instance
        """
        return response_serializer(TeamSerializer, pk=pk, object_class=Team)

    @swagger_auto_schema(
        request_body=TeamSerializer,
        responses={
            400: 'JSON parse error'
        })
    def put(self, request, pk):
        """
        Update a team instance
        """
        data = JSONParser().parse(request)
        return response_serializer(TeamSerializer, pk=pk, object_class=Team, data=data, partial=True)


class UsersByTeamsList(APIView):
    """
    Return a list of users by a specific team
    """
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        team = get_team_by_pk(pk)
        users = GovUser.objects.filter(team=team)
        return response_serializer(GovUserViewSerializer, obj=users, many=True, response_name='users')
