from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from end_user.libraries.get_end_user import get_end_user
from queries.end_user_advisories.models import EndUserAdvisoryQuery
from static.countries.models import Country
from static.countries.serializers import CountrySerializer
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_from_status


class EndUserAdvisoriesList(APIView):
    def get(self, request):
        countries = Country.objects.all()
        serializer = CountrySerializer(countries, many=True)
        return JsonResponse(data={'end_user_advisories': serializer.data})

    def post(self, request):
        """
        Create a new End User Advisory Enquiry query case instance
        """
        data = JSONParser().parse(request)
        end_user = get_end_user(data['end_user_id'])

        euae_query = EndUserAdvisoryQuery(details=data['details'],
                                          raised_reason=data['raised_reason'],
                                          end_user=end_user,
                                          status=get_case_status_from_status(CaseStatusEnum.SUBMITTED))

        euae_query.save()

        # # Should be added to enforcement unit queue in the future
        # queue = Queue.objects.get(pk='00000000-0000-0000-0000-000000000001')
        # queue.cases.add(case)
        # queue.save()

        return JsonResponse(data={'id': euae_query.id}, status=status.HTTP_201_CREATED)
