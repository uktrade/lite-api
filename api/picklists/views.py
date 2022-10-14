from django.db.models import BinaryField, Case, When
from django.http.response import JsonResponse

from rest_framework import status, permissions
from rest_framework.decorators import permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.audit_trail.serializers import AuditSerializer
from api.core.authentication import GovAuthentication
from api.core.constants import GovPermissions
from api.core.custom_views import OptionalPaginationView
from api.core.helpers import str_to_bool
from api.core.permissions import assert_user_has_permission
from lite_content.lite_api import strings
from api.picklists.enums import PickListStatus
from api.picklists.helpers import get_picklist_item
from api.picklists.models import PicklistItem
from api.picklists.serializers import (
    PicklistUpdateCreateSerializer,
    PicklistListSerializer,
    TinyPicklistSerializer,
)


class PickListsPaginator(PageNumberPagination):
    page_size = 100


@permission_classes((permissions.AllowAny,))
class PickListsView(OptionalPaginationView):
    authentication_classes = (GovAuthentication,)
    serializer_class = PicklistListSerializer
    pagination_class = PickListsPaginator

    def get_serializer_class(self):
        if str_to_bool(self.request.GET.get("disable_pagination")):
            return TinyPicklistSerializer
        else:
            return PicklistListSerializer

    def get_queryset(self):
        """
        Returns a list of all picklist items, filtered by type and by show_deactivated
        """
        picklist_items = PicklistItem.objects.filter(
            team=self.request.user.govuser.team,
        )

        picklist_type = self.request.GET.get("type")
        name = self.request.GET.get("name")
        show_deactivated = str_to_bool(self.request.GET.get("show_deactivated"))
        ids = self.request.GET.get("ids")

        if picklist_type:
            picklist_items = picklist_items.filter(type=picklist_type)

        if not show_deactivated:
            picklist_items = picklist_items.filter(status=PickListStatus.ACTIVE)

        if ids:
            ids = ids.split(",")
            picklist_items = picklist_items.filter(id__in=ids)

        if name:
            picklist_items = picklist_items.filter(name__icontains=name)
            picklist_items = picklist_items.annotate(
                is_prefixed=Case(
                    When(name__istartswith=name.lower(), then=True),
                    default=False,
                    output_field=BinaryField(),
                ),
            )
            return picklist_items.order_by("-is_prefixed", "name")

        return picklist_items.order_by("name")

    def post(self, request):
        """
        Add a new picklist item
        """
        assert_user_has_permission(self.request.user.govuser, GovPermissions.MANAGE_PICKLISTS)
        data = JSONParser().parse(request)
        data["team"] = request.user.govuser.team.id
        serializer = PicklistUpdateCreateSerializer(data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            audit_trail_service.create(
                actor=request.user,
                verb=AuditType.CREATED_PICKLIST,
                target=serializer.instance,
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

        audit_qs = audit_trail_service.get_activity_for_user_and_model(request.user, picklist_item)
        data["activity"] = AuditSerializer(audit_qs, many=True).data

        return JsonResponse(data={"picklist_item": data})

    def put(self, request, pk):
        """
        Edit status of a new picklist item
        """
        assert_user_has_permission(self.request.user.govuser, GovPermissions.MANAGE_PICKLISTS)
        picklist_item = get_picklist_item(pk)

        if request.user.govuser.team != picklist_item.team:
            return JsonResponse(
                data={"errors": strings.Picklists.FORBIDDEN},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = PicklistUpdateCreateSerializer(instance=picklist_item, data=request.data, partial=True)

        if serializer.is_valid():
            if serializer.validated_data.get("text"):
                if picklist_item.text != serializer.validated_data["text"]:
                    audit_trail_service.create(
                        actor=request.user,
                        verb=AuditType.UPDATED_PICKLIST_TEXT,
                        target=serializer.instance,
                        payload={
                            "old_text": picklist_item.text,
                            "new_text": serializer.validated_data["text"],
                        },
                    )

            if serializer.validated_data.get("name"):
                if picklist_item.name != serializer.validated_data["name"]:
                    audit_trail_service.create(
                        actor=request.user,
                        verb=AuditType.UPDATED_PICKLIST_NAME,
                        target=serializer.instance,
                        payload={
                            "old_name": picklist_item.name,
                            "new_name": serializer.validated_data["name"],
                        },
                    )

            if serializer.validated_data.get("status"):
                picklist_status = serializer.validated_data["status"]
                if picklist_item.status != picklist_status:
                    if picklist_status == PickListStatus.DEACTIVATED:
                        audit_trail_service.create(
                            actor=request.user,
                            verb=AuditType.DEACTIVATE_PICKLIST,
                            target=serializer.instance,
                        )
                    else:
                        audit_trail_service.create(
                            actor=request.user,
                            verb=AuditType.REACTIVATE_PICKLIST,
                            target=serializer.instance,
                        )

            serializer.save()
            return JsonResponse(data={"picklist_item": serializer.data})

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
