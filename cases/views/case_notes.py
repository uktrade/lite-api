from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from lite_content.lite_api import cases
from audit_trail import service
from audit_trail.payload import AuditType
from cases.libraries.get_case import get_case
from cases.libraries.get_case_note import get_case_notes_from_case
from cases.libraries.mark_notifications_as_viewed import mark_notifications_as_viewed
from cases.serializers import CaseNoteSerializer
from conf.authentication import SharedAuthentication

from static.statuses.enums import CaseStatusEnum
from users.models import ExporterUser


class CaseNoteList(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request, pk):
        """ Gets all case notes. """
        case = get_case(pk)
        case_notes = get_case_notes_from_case(case, isinstance(request.user, ExporterUser))
        serializer = CaseNoteSerializer(case_notes, many=True)

        mark_notifications_as_viewed(request.user, case_notes)

        return JsonResponse(data={"case_notes": serializer.data})

    def post(self, request, pk):
        """ Create a case note on a case. """
        case = get_case(pk)

        if CaseStatusEnum.is_terminal(case.status.status) and isinstance(request.user, ExporterUser):
            return JsonResponse(
                data={
                    "errors": {
                        "text": [cases.System.TERMINAL_CASE_CANNOT_PERFORM_OPERATION_ERROR]
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = request.data
        data["case"] = str(case.id)
        data["user"] = str(request.user.id)

        serializer = CaseNoteSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            service.create(
                verb=AuditType.CREATED_CASE_NOTE,
                actor=request.user,
                action_object=serializer.instance,
                target=case,
                payload={"case_note": serializer.instance.text},
            )
            return JsonResponse(data={"case_note": serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
