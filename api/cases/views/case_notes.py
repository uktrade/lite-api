from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView

from api.audit_trail import service
from api.audit_trail.enums import AuditType
from api.cases.libraries.get_case import get_case
from api.cases.libraries.get_case_note import get_case_notes_from_case
from api.cases.libraries.delete_notifications import delete_exporter_notifications
from api.cases.serializers import CaseNoteSerializer, CaseNoteMentionsSerializer
from api.core.authentication import SharedAuthentication, GovAuthentication
from lite_content.lite_api import strings
from api.organisations.libraries.get_organisation import get_request_user_organisation_id
from api.staticdata.statuses.enums import CaseStatusEnum
from api.cases.models import CaseNoteMentions


class CaseNoteList(APIView):
    authentication_classes = (SharedAuthentication,)
    serializer = CaseNoteSerializer

    def get(self, request, pk):
        """Gets all case notes."""
        is_user_exporter = hasattr(request.user, "exporteruser")
        case_notes = get_case_notes_from_case(pk, only_show_notes_visible_to_exporter=is_user_exporter)
        if is_user_exporter:
            delete_exporter_notifications(
                user=request.user.exporteruser,
                organisation_id=get_request_user_organisation_id(request),
                objects=case_notes,
            )

        serializer = self.serializer(case_notes, many=True)
        return JsonResponse(data={"case_notes": serializer.data})

    def post(self, request, pk):
        """Create a case note on a case."""
        case = get_case(pk, hasattr(request.user, "exporteruser"))
        if CaseStatusEnum.is_terminal(case.status.status) and hasattr(request.user, "exporteruser"):
            return JsonResponse(
                data={"errors": {"text": [strings.Applications.Generic.TERMINAL_CASE_CANNOT_PERFORM_OPERATION_ERROR]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = request.data
        mentions_data = data.pop("mentions", None)
        data["case"] = str(case.id)
        data["user"] = str(request.user.pk)
        serializer = self.serializer(data=data)
        returned_data = {}
        if serializer.is_valid():
            serializer.save()
            returned_data = serializer.data
            service.create(
                verb=AuditType.CREATED_CASE_NOTE,
                actor=request.user,
                action_object=serializer.instance,
                target=case,
                payload={"additional_text": serializer.instance.text},
                ignore_case_status=True,
            )
        else:
            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        # Let create case note mentions

        if mentions_data:
            update = {"case_note": str(serializer.instance.id)}
            mentions_data = [{**m, **update} for m in mentions_data]
            case_note_mentions = CaseNoteMentionsSerializer(data=mentions_data, many=True)
            if case_note_mentions.is_valid():
                case_note_mentions.save()
                returned_data.update({"mentions": case_note_mentions.data})
            else:
                return JsonResponse(data={"errors": case_note_mentions.errors}, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse(data={"case_note": returned_data}, status=status.HTTP_201_CREATED)


class CaseNoteMentionList(ListAPIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = CaseNoteMentionsSerializer

    def get_queryset(self):
        return (
            CaseNoteMentions.objects.select_related(
                "case_note",
                "user",
                "case_note__user",
                "case_note__user__govuser__team",
                "case_note__case",
            )
            .filter(case_note__case_id=self.kwargs["pk"])
            .order_by("-created_at")
        )


class UserCaseNoteMention(APIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = CaseNoteMentionsSerializer

    def get(self, request):
        """Gets all mentions for user."""
        qs = (
            CaseNoteMentions.objects.select_related(
                "case_note",
                "user",
                "case_note__user",
                "case_note__user__govuser__team",
                "case_note__case",
            )
            .filter(user_id=request.user.pk)
            .order_by("-created_at")
        )
        serializer = self.serializer_class(qs, many=True)

        return JsonResponse(data={"mentions": serializer.data})
