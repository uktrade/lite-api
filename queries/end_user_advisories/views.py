import json

import reversion
from django.http import JsonResponse
from rest_framework import status, serializers
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from cases.libraries.activity_types import CaseActivityType
from cases.models import CaseActivity
from conf.authentication import ExporterAuthentication, GovAuthentication
from conf.constants import Permissions
from conf.permissions import has_permission
from queries.end_user_advisories.models import EndUserAdvisoryQuery
from queries.end_user_advisories.serializers import EndUserAdvisorySerializer
from queries.end_user_advisories.libraries.get_end_user_advisory import get_end_user_advisory_by_pk
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_from_status


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

        if not data.get('end_user'):
            data['end_user'] = {}

        data['organisation'] = request.user.organisation.id
        data['end_user']['organisation'] = request.user.organisation.id

        serializer = EndUserAdvisorySerializer(data=data)

        try:
            if serializer.is_valid():
                if 'validate_only' not in data or data['validate_only'] == 'False':
                    serializer.save()
                    return JsonResponse(data={'end_user_advisory': serializer.data},
                                        status=status.HTTP_201_CREATED)
                else:
                    return JsonResponse(data={}, status=status.HTTP_200_OK)

            return JsonResponse(data={'errors': serializer.errors},
                                status=status.HTTP_400_BAD_REQUEST)
        except serializers.ValidationError as e:
            return JsonResponse(data={'errors': e},
                                status=status.HTTP_400_BAD_REQUEST)


class EndUserAdvisoriesDetail(APIView):
    authentication_classes = (GovAuthentication,)

    def put(self, request, pk):
        """
        Update an end user advisory instance.
        """
        end_user_advisory = get_end_user_advisory_by_pk(pk)

        with reversion.create_revision():
            data = json.loads(request.body)

            # Only allow the final decision if the user has the MAKE_FINAL_DECISIONS permission
            if data.get('status') == CaseStatusEnum.APPROVED or data.get('status') == CaseStatusEnum.DECLINED:
                has_permission(request.user, Permissions.MAKE_FINAL_DECISIONS)

            request.data['status'] = str(get_case_status_from_status(data.get('status')).pk)

            serializer = EndUserAdvisorySerializer(end_user_advisory, data=request.data, partial=True)

            if serializer.is_valid():
                CaseActivity.create(activity_type=CaseActivityType.UPDATED_STATUS,
                                    case=end_user_advisory.case.get(),
                                    user=request.user,
                                    status=data.get('status'))

                serializer.save()
                return JsonResponse(data={'end_user_advisory': serializer.data})

            return JsonResponse(data={'errors': serializer.errors}, status=400)
