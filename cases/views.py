from django.http.response import JsonResponse
from rest_framework import permissions, status
from rest_framework.decorators import permission_classes
from rest_framework.views import APIView
from reversion.models import Version

from cases.libraries.activity_helpers import convert_audit_to_activity, convert_case_note_to_activity
from cases.libraries.get_case import get_case
from cases.libraries.get_case_note import get_case_notes_from_case
from cases.serializers import CaseSerializer, CaseNoteCreateSerializer, CaseNoteViewSerializer
from conf.authentication import GovAuthentication


@permission_classes((permissions.AllowAny,))
class CaseDetail(APIView):
    authentication_classes = (GovAuthentication,)
    """
    Retrieve a case instance.
    """

    def get(self, request, pk):
        case = get_case(pk)
        serializer = CaseSerializer(case)
        return JsonResponse(data={'case': serializer.data})


class CaseNoteList(APIView):
    authentication_classes = (GovAuthentication,)
    """
    Retrieve/create case notes.
    """

    def get(self, request, pk):
        case = get_case(pk)
        serializer = CaseNoteSerializer(get_case_notes_from_case(case), many=True)
        return JsonResponse(data={'case_notes': serializer.data})

    def post(self, request, pk):
        case = get_case(pk)
        data = request.data
        data['case'] = str(case.id)
        data['user'] = str(request.user.id)

        serializer = CaseNoteSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'case_note': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class ActivityList(APIView):
    authentication_classes = (EmailAuthentication,)
    """
    Retrieves all activity related to a case:
    * Case Notes
    * Case Updates
    """

    def get(self, request, pk):
        case = get_case(pk)
        case_notes = get_case_notes_from_case(case)
        version_records = Version.objects.filter(object_id=case.application.pk).order_by('-revision_id')
        activity = []

        # Split fields into request fields
        fields = request.GET.get('fields', None)
        if fields:
            fields = fields.split(',')

        for version in version_records:
            activity.append(convert_audit_to_activity(version))

        if fields:
            for item in activity:
                item['data'] = {your_key: item['data'][your_key] for your_key in fields}

            # Only show unique dictionaries
            for i in range(len(activity)):
                if i < len(activity) - 1:
                    activity[i]['data'] = dict(set(activity[i]['data'].items()) - set(activity[i + 1]['data'].items()))

                    if not activity[i]['data']:
                        del activity[i]

        # Remove the last update as it is the application creation
        if len(activity):
            del activity[-1]

        for case_note in case_notes:
            activity.append(convert_case_note_to_activity(case_note))

        # Sort the activity based on date (newest first)
        activity.sort(key=lambda x: x['date'], reverse=True)

        return JsonResponse(data={'activity': activity})
