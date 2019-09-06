import reversion
from django.http import JsonResponse
from rest_framework import permissions, status
from rest_framework.decorators import permission_classes
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import GovAuthentication
from content_strings.strings import get_string
from flags.enums import FlagStatuses
from flags.helpers import get_object_of_level
from flags.libraries.get_flag import get_flag
from flags.models import Flag
from flags.serializers import FlagSerializer, FlagAssignmentSerializer


@permission_classes((permissions.AllowAny,))
class FlagsList(APIView):
    """
    List all flags and perform actions on the list
    """
    authentication_classes = (GovAuthentication,)

    def get(self, request):
        """
        Returns list of all flags
        """
        level = request.GET.get('level', None)
        if level:
            level = level[:-1].title()
            flags = Flag.objects.filter(level=level)
        else:
            flags = Flag.objects.all()

        team = request.GET.get('team', None)
        if team:
            team_id = request.user.team.id
            flags = flags.filter(team=team_id)

        flags = flags.order_by('name')
        serializer = FlagSerializer(flags, many=True)
        return JsonResponse(data={'flags': serializer.data})

    def post(self, request):
        """
        Add a new flag
        """
        data = JSONParser().parse(request)
        data['team'] = request.user.team.id
        serializer = FlagSerializer(data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'flag': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


@permission_classes((permissions.AllowAny,))
class FlagDetail(APIView):
    """
    Details of a specific flag
    """
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Returns details of a specific flag
        """
        flag = get_flag(pk)
        serializer = FlagSerializer(flag)
        return JsonResponse(data={'flag': serializer.data})

    def put(self, request, pk):
        """
        Edit details of a specific flag
        """
        flag = get_flag(pk)

        # Prevent a user changing a flag if it does not belong to their team
        if request.user.team != flag.team:
            return JsonResponse(data={'errors': get_string('flags.error_messages.forbidden')},
                                status=status.HTTP_403_FORBIDDEN)

        serializer = FlagSerializer(instance=flag, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'flag': serializer.data})

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class AssignFlags(APIView):
    authentication_classes = (GovAuthentication,)

    def put(self, request):
        data = JSONParser().parse(request)
        level = data.get('level')[:-1].title()
        response_data = []

        for pk in data.get('objects'):
            object = get_object_of_level(level, pk)
            serializer = FlagAssignmentSerializer(data=data, context={'team': request.user.team, 'level': level})

            if serializer.is_valid():
                self._assign_flags(serializer.validated_data.get('flags'), level, serializer.validated_data.get('note'), object, request.user)
                response_data.append({level.lower(): serializer.data})
            else:
                return JsonResponse(data={'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse(data=response_data, status=status.HTTP_200_OK, safe=False)

    def _assign_flags(self, validated_data, level, note, object, user):
        previously_assigned_team_flags = object.flags.filter(level=level, team=user.team)
        previously_assigned_deactivated_team_flags = object.flags.filter(level=level, team=user.team, status=FlagStatuses.DEACTIVATED)
        previously_assigned_not_team_flags = object.flags.exclude(level=level, team=user.team)
        add_flags = [flag.name for flag in validated_data if flag not in previously_assigned_team_flags]
        ignored_flags = validated_data + [x for x in previously_assigned_deactivated_team_flags]
        remove_flags = [flag.name for flag in previously_assigned_team_flags if flag not in ignored_flags]

        with reversion.create_revision():
            reversion.set_comment(
                ('{"flags": {"removed": ' + str(remove_flags) + ', "added": ' + str(add_flags) + ', "note": "' + str(note) + '"}}')
                .replace('\'', '"')
            )
            reversion.set_user(user)

            object.flags.set(validated_data + list(previously_assigned_not_team_flags) + list(previously_assigned_deactivated_team_flags))
