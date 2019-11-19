from django.http import JsonResponse
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import GovAuthentication
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

    @swagger_auto_schema(
        responses={200: openapi.Response("OK", TeamSerializer),}
    )
    def get(self, request):
        """
        List all teams
        """
        teams = Team.objects.all().order_by("name")

        serializer = TeamSerializer(teams, many=True)
        return JsonResponse(data={"teams": serializer.data})

    @swagger_auto_schema(request_body=TeamSerializer, responses={400: "JSON parse error"})
    def post(self, request):
        """
        Create a new team
        """
        data = JSONParser().parse(request)

        serializer = TeamSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={"team": serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class TeamDetail(APIView):
    """
    Perform action on a single team
    """

    authentication_classes = (GovAuthentication,)

    def get_object(self, pk):
        return get_team_by_pk(pk)

    @swagger_auto_schema(
        responses={200: openapi.Response("OK", TeamSerializer),}
    )
    def get(self, request, pk):
        """
        Retrieve a team instance
        """
        team = get_team_by_pk(pk)

        serializer = TeamSerializer(team)
        return JsonResponse(data={"team": serializer.data})

    @swagger_auto_schema(request_body=TeamSerializer, responses={400: "JSON parse error"})
    def put(self, request, pk):
        """
        Update a team instance
        """
        data = JSONParser().parse(request)
        serializer = TeamSerializer(self.get_object(pk), data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={"team": serializer.data})

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class UsersByTeamsList(APIView):
    """
    Return a list of users by a specific team
    """

    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        team = get_team_by_pk(pk)
        users = GovUser.objects.filter(team=team)

        serializer = GovUserViewSerializer(users, many=True)
        return JsonResponse(data={"users": serializer.data})
