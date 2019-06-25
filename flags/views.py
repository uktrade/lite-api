from django.http import JsonResponse, Http404
from rest_framework import permissions, status
from rest_framework.decorators import permission_classes
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import GovAuthentication
from content_strings.strings import get_string
from flags.libraries.get_flag import get_flag
from flags.models import Flag
from flags.serializers import FlagSerializer


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
        flags = Flag.objects.filter().order_by('name')
        serializer = FlagSerializer(flags, many=True)
        return JsonResponse(data={'flags': serializer.data})

    def post(self, request):
        """
        Add a new flag
        """
        data = JSONParser().parse(request)
        data['team'] = request.user.team.id
        data['name'] = data['name'].strip()
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
        data = request.data.copy()
        if request.user.team != flag.team:
            return JsonResponse(data={'errors': get_string('flags.error_messages.forbidden')},
                                status=status.HTTP_403_FORBIDDEN)
        serializer = FlagSerializer(instance=flag, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'flag': serializer.data})
        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
