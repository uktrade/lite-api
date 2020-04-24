from django.http.response import JsonResponse
from rest_framework import status, permissions
from rest_framework.decorators import permission_classes
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from audit_trail import service as audit_trail_service
from audit_trail.payload import AuditType
from audit_trail.serializers import AuditSerializer
from conf.authentication import GovAuthentication
from conf.custom_views import OptionalPaginationView
from conf.helpers import str_to_bool
from lite_content.lite_api import strings
from picklists.enums import PickListStatus
from picklists.helpers import get_picklist_item
from picklists.models import PicklistItem
from picklists.serializers import (
    PicklistUpdateCreateSerializer,
    PicklistListSerializer,
    TinyPicklistSerializer,
)


@permission_classes((permissions.AllowAny,))
class PickListsView(OptionalPaginationView):
    authentication_classes = (GovAuthentication,)
    serializer_class = PicklistListSerializer

    def get_serializer_class(self):
        if str_to_bool(self.request.GET.get("disable_pagination")):
            return TinyPicklistSerializer
        else:
            return PicklistListSerializer

    def get_queryset(self):
        """
        Returns a list of all picklist items, filtered by type and by show_deactivated
        """
        picklist_items = PicklistItem.objects.filter(team=self.request.user.team,)

        picklist_type = self.request.GET.get("type")
        show_deactivated = str_to_bool(self.request.GET.get("show_deactivated"))
        ids = self.request.GET.get("ids")

        if picklist_type:
            picklist_items = picklist_items.filter(type=picklist_type)

        if not show_deactivated:
            picklist_items = picklist_items.filter(status=PickListStatus.ACTIVE)

        if ids:
            ids = ids.split(",")
            picklist_items = picklist_items.filter(id__in=ids)

        return picklist_items.order_by("-updated_at")

    def post(self, request):
        """
        Add a new picklist item
        """
        data = JSONParser().parse(request)
        data["team"] = request.user.team.id
        serializer = PicklistUpdateCreateSerializer(data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            audit_trail_service.create(
                actor=request.user, verb=AuditType.CREATED_PICKLIST, target=serializer.instance,
            )
            return JsonResponse(data={"picklist_item": serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@permission_classes((permissions.AllowAny,))
class PicklistItemDetail(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Gets details of a specific picklist item
        """
        picklist_item = get_picklist_item(pk)
        data = PicklistListSerializer(picklist_item).data

        audit_qs = audit_trail_service.get_user_obj_trail_qs(request.user, picklist_item)
        data["activity"] = AuditSerializer(audit_qs, many=True).data

        return JsonResponse(data={"picklist_item": data})

    def put(self, request, pk):
        """
        Edit status of a new picklist item
        """
        picklist_item = get_picklist_item(pk)

        if request.user.team != picklist_item.team:
            return JsonResponse(data={"errors": strings.Picklists.FORBIDDEN}, status=status.HTTP_403_FORBIDDEN,)

        serializer = PicklistUpdateCreateSerializer(instance=picklist_item, data=request.data, partial=True)

        if serializer.is_valid():
            if serializer.validated_data.get("text"):
                if picklist_item.text != serializer.validated_data["text"]:
                    audit_trail_service.create(
                        actor=request.user,
                        verb=AuditType.UPDATED_PICKLIST_TEXT,
                        target=serializer.instance,
                        payload={"old_text": picklist_item.text, "new_text": serializer.validated_data["text"],},
                    )

            if serializer.validated_data.get("name"):
                if picklist_item.name != serializer.validated_data["name"]:
                    audit_trail_service.create(
                        actor=request.user,
                        verb=AuditType.UPDATED_PICKLIST_NAME,
                        target=serializer.instance,
                        payload={"old_name": picklist_item.name, "new_name": serializer.validated_data["name"],},
                    )

            if serializer.validated_data.get("status"):
                picklist_status = serializer.validated_data["status"]
                if picklist_item.status != picklist_status:
                    if picklist_status == PickListStatus.DEACTIVATED:
                        audit_trail_service.create(
                            actor=request.user, verb=AuditType.DEACTIVATE_PICKLIST, target=serializer.instance,
                        )
                    else:
                        audit_trail_service.create(
                            actor=request.user, verb=AuditType.REACTIVATE_PICKLIST, target=serializer.instance,
                        )

            serializer.save()
            return JsonResponse(data={"picklist_item": serializer.data})

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
