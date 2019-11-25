from actstream.models import Action
from django.http import JsonResponse
from rest_framework.views import APIView

from audit_trail.serializers import ActivitySerializer
from cases.libraries.get_case import get_case, get_case_activity
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
        # activity.extend(convert_case_notes_to_activity(get_case_notes_from_case(case, False)))
        #
        # # Sort the activity based on date (newest first)
        # activity.sort(key=lambda x: x.created_at, reverse=True)


        actions = Action.objects.all()

        serializer = ActivitySerializer(actions, many=True)


        return JsonResponse(data={"activity": serializer.data})
