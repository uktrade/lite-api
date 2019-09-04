from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import ExporterAuthentication
from queries.end_user_advisories.models import EndUserAdvisoryQuery
from queries.end_user_advisories.serializers import EndUserAdvisorySerializer


class EndUserAdvisoriesList(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request):
        end_user_advisories = EndUserAdvisoryQuery.objects.filter(end_user__organisation=request.user.organisation)
        serializer = EndUserAdvisorySerializer(end_user_advisories, many=True)
        return JsonResponse(data={'end_user_advisories': serializer.data})

    def post(self, request):
        """
        Create a new End User Advisory Enquiry query case instance
        """
        data = JSONParser().parse(request)
        data['end_user']['organisation'] = request.user.organisation.id

        print(data)

        serializer = EndUserAdvisorySerializer(data=data)

        if serializer.is_valid():
            if 'validate_only' not in data or not data['validate_only']:
                serializer.save()

                return JsonResponse(data={'end_user_advisory': serializer.data},
                                    status=status.HTTP_201_CREATED)
            else:
                return JsonResponse(data={}, status=status.HTTP_200_OK)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
