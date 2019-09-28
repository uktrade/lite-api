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
from conf.serializers import response_serializer
from content_strings.strings import get_string
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
        picklist_type = request.GET.get('type', None)
        show_deactivated = str_to_bool(request.GET.get('show_deactivated', None))
        query = [Q(team=request.user.team.id)]

        if picklist_type:
            query.append(Q(type=picklist_type))

        if not show_deactivated:
            query.append(Q(status=PickListStatus.ACTIVE))

        picklist_items = PicklistItem.objects.filter(reduce(operator.and_, query))
        return response_serializer(PicklistSerializer, obj=picklist_items, many=True)

    def post(self, request):
        """
        Add a new picklist item
        """
        data = JSONParser().parse(request)
        data['team'] = request.user.team.id
        return response_serializer(PicklistSerializer, data=data, partial=True, response_name='picklist_item')


@permission_classes((permissions.AllowAny,))
class PicklistItemDetail(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Gets details of a specific picklist item
        """
        return response_serializer(PicklistSerializer, pk=pk, object_class=PicklistItem)

    def put(self, request, pk):
        """
        Edit status of a new picklist item
        """
        picklist_item = get_picklist_item(pk)

        if request.user.team != picklist_item.team:
            return JsonResponse(data={'errors': get_string('picklist_items.error_messages.forbidden')},
                                status=status.HTTP_403_FORBIDDEN)

        return response_serializer(PicklistSerializer, obj=picklist_item, data=request.data, partial=True)
