from django.http import JsonResponse
from rest_framework import status, permissions
from rest_framework.decorators import permission_classes
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView
from conf.authentication import GovAuthentication
from ecju_queries.libraries.get_ecju_query import get_ecju_query
from ecju_queries.serializers import EcjuQuerySerializer, EcjuQueryCreateSerializer


@permission_classes((permissions.AllowAny,))
class EcjuQueriesList(APIView):
    authentication_classes = (GovAuthentication,)

    def post(self, request):
        """
        Add a new ECJU query
        """
        data = JSONParser().parse(request)
        data['raised_by_user'] = request.user.id
        serializer = EcjuQueryCreateSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'ecju_query_id': serializer.data['id']},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


@permission_classes((permissions.AllowAny,))
class EcjuQueryDetail(APIView):
    """
    Details of a specific ECJU query
    """
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Returns details of a specific flag
        """
        ecju_query = get_ecju_query(pk)
        serializer = EcjuQuerySerializer(ecju_query)
        return JsonResponse(data={'ecju_query': serializer.data})
