from django.http.response import JsonResponse
from rest_framework import permissions, status
from rest_framework.decorators import permission_classes
from rest_framework.views import APIView

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

