from django.http import JsonResponse
from rest_framework import status, permissions
from rest_framework.decorators import permission_classes
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import GovAuthentication
from ecju_queries.serializers import EcjuQuerySerializer


@permission_classes((permissions.AllowAny,))
class EcjuQueriesList(APIView):
    authentication_classes = (GovAuthentication,)

    def post(self, request):
        """
        Add a new ECJU query
        """
        data = JSONParser().parse(request)
        serializer = EcjuQuerySerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'ecju_query_id': serializer.data['id']},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
