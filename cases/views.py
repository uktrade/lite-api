import json

from django.http.response import JsonResponse
from rest_framework import permissions, status
from rest_framework.decorators import permission_classes
from rest_framework.views import APIView
from reversion.models import Version, Revision

from cases.libraries.activity_helpers import convert_audit_to_activity, convert_case_note_to_activity
from cases.libraries.get_case import get_case
from cases.libraries.get_case_note import get_case_notes_from_case
from cases.serializers import CaseSerializer, CaseNoteCreateSerializer, CaseNoteViewSerializer


@permission_classes((permissions.AllowAny,))
class CaseDetail(APIView):
    """
    Retrieve a case instance.
    """
    def get(self, request, pk):
        case = get_case(pk)
        serializer = CaseSerializer(case)
        return JsonResponse(data={'case': serializer.data})


@permission_classes((permissions.AllowAny,))
class CaseNoteList(APIView):
    """
    Retrieve/create case notes.
    """
    def get(self, request, pk):
        case = get_case(pk)
        serializer = CaseNoteViewSerializer(get_case_notes_from_case(case), many=True)
        return JsonResponse(data={'case_notes': serializer.data})

    def post(self, request, pk):
        case = get_case(pk)
        data = request.data
        data['case'] = str(case.id)
        serializer = CaseNoteCreateSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'case_note': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


@permission_classes((permissions.AllowAny,))
class ActivityList(APIView):
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

        for version in version_records:
            activity.append(convert_audit_to_activity(version))

        for case_note in case_notes:
            activity.append(convert_case_note_to_activity(case_note))

        # Sort the activity based on date (newest first)
        activity.sort(key=lambda item: item['date'], reverse=True)

        return JsonResponse(data={'activity': activity})

