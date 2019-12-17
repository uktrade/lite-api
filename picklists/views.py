import lite_content.lite_api.picklists
from lite_content.lite_api import strings
import operator
from functools import reduce

from django.db.models import Q
from django.http.response import JsonResponse
from rest_framework import status, permissions
from rest_framework.decorators import permission_classes
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import GovAuthentication
from conf.helpers import str_to_bool
from picklists.enums import PickListStatus
from picklists.helpers import get_picklist_item
from picklists.models import PicklistItem
from picklists.serializers import PicklistSerializer


@permission_classes((permissions.AllowAny,))
class PickListItems(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request):
        """
        Returns a list of all picklist items, filtered by type and by show_deactivated
        """
        picklist_type = request.GET.get("type", None)
        show_deactivated = str_to_bool(request.GET.get("show_deactivated", None))
        ids = request.GET.get("ids", None)
        query = [Q(team=request.user.team.id)]

        if picklist_type:
            query.append(Q(type=picklist_type))

        if not show_deactivated:
            query.append(Q(status=PickListStatus.ACTIVE))

        if ids:
            ids = ids.split(",")
            query.append(Q(id__in=ids))

        picklist_items = PicklistItem.objects.filter(reduce(operator.and_, query))
        picklist_items = picklist_items.order_by("-last_modified_at")
        serializer = PicklistSerializer(picklist_items, many=True)
        return JsonResponse(data={"picklist_items": serializer.data})

    def post(self, request):
        """
        Add a new picklist item
        """
        data = JSONParser().parse(request)
        data["team"] = request.user.team.id
        serializer = PicklistSerializer(data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
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
        serializer = PicklistSerializer(picklist_item)
        return JsonResponse(data={"picklist_item": serializer.data})

    def put(self, request, pk):
        """
        Edit status of a new picklist item
        """
        picklist_item = get_picklist_item(pk)

        if request.user.team != picklist_item.team:
            return JsonResponse(
                data={"errors": lite_content.lite_api.picklists.Picklists.FORBIDDEN}, status=status.HTTP_403_FORBIDDEN,
            )

        serializer = PicklistSerializer(instance=picklist_item, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={"picklist_item": serializer.data})

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
