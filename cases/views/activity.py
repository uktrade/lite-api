from django.http import JsonResponse
from rest_framework.views import APIView

from cases.libraries.activity_helpers import convert_case_notes_to_activity
from cases.libraries.get_case import get_case, get_case_activity
from cases.libraries.get_case_note import get_case_notes_from_case
from cases.serializers import CaseActivitySerializer
from conf.authentication import GovAuthentication


class Activity(APIView):
    authentication_classes = (GovAuthentication,)
    """
    Retrieves all activity related to a case
    * Case Updates
    * Case Notes
    * ECJU Queries
    """

    def get(self, request, pk):
        case = get_case(pk)
        activity = get_case_activity(case)
        activity.extend(convert_case_notes_to_activity(get_case_notes_from_case(case, False)))

        # Sort the activity based on date (newest first)
        activity.sort(key=lambda x: x.created_at, reverse=True)

        serializer = CaseActivitySerializer(activity, many=True)
        return JsonResponse(data={"activity": serializer.data})
