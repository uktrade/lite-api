from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from audit_trail import service
from audit_trail.enums import AuditType
from cases.libraries.get_case import get_case
from cases.libraries.get_case_note import get_case_notes_from_case
from cases.libraries.delete_notifications import delete_exporter_notifications
from cases.serializers import CaseNoteSerializer
from conf.authentication import SharedAuthentication
from lite_content.lite_api import strings
from organisations.libraries.get_organisation import get_request_user_organisation_id
from static.statuses.enums import CaseStatusEnum
from users.models import ExporterUser


class CaseNoteList(APIView):
    authentication_classes = (SharedAuthentication,)
    serializer = CaseNoteSerializer

    def get(self, request, pk):
        """ Gets all case notes. """
        is_user_exporter = isinstance(request.user, ExporterUser)
        case_notes = get_case_notes_from_case(pk, only_show_notes_visible_to_exporter=is_user_exporter)

        if is_user_exporter:
            delete_exporter_notifications(
                user=request.user, organisation_id=get_request_user_organisation_id(request), objects=case_notes
            )

        serializer = self.serializer(case_notes, many=True)
        return JsonResponse(data={"case_notes": serializer.data})

    def post(self, request, pk):
        """ Create a case note on a case. """
        case = get_case(pk, isinstance(request.user, ExporterUser))

        if CaseStatusEnum.is_terminal(case.status.status) and isinstance(request.user, ExporterUser):
            return JsonResponse(
                data={"errors": {"text": [strings.Applications.Generic.TERMINAL_CASE_CANNOT_PERFORM_OPERATION_ERROR]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = request.data
        data["case"] = str(case.id)
        data["user"] = str(request.user.id)

        serializer = self.serializer(data=data)

        if serializer.is_valid():
            serializer.save()
            service.create(
                verb=AuditType.CREATED_CASE_NOTE,
                actor=request.user,
                action_object=serializer.instance,
                target=case,
                payload={"additional_text": serializer.instance.text},
                ignore_case_status=True,
            )
            return JsonResponse(data={"case_note": serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
