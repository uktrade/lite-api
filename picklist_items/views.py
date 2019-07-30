from django.shortcuts import render
from rest_framework.views import APIView
from conf.authentication import GovAuthentication
from picklist_items.models import PicklistItem
from django.http.response import JsonResponse
from rest_framework import status, permissions
from rest_framework.parsers import JSONParser
from picklist_items.libraries.get_picklist_item import get_picklist_item
from picklist_items.serializers import PicklistSerializer
from content_strings.strings import get_string
from rest_framework.decorators import permission_classes


@permission_classes((permissions.AllowAny,))
class PickListItems(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request):
        """
        Returns a list of all picklist items, filtered by type
        """
        type = request.GET.get('type', None)
        if type:
            picklist_items = PicklistItem.objects.filter(type=type)
        else:
            picklist_items = PicklistItem.objects.filter()

        serializer = PicklistSerializer(picklist_items, many=True)

        return JsonResponse(data={'picklist_items': serializer.data})

    def post(self, request):
        """
        Add a new picklist item
        """
        data = JSONParser().parse(request)
        data['team'] = request.user.team.id
        serializer = PicklistSerializer(data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'picklist_item': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


@permission_classes((permissions.AllowAny,))
class PicklistItemDetail(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Gets details of a specific picklist item
        """
        picklist_item = get_picklist_item(pk)
        serializer = PicklistSerializer(picklist_item)
        return JsonResponse(data={'picklist_item': serializer.data})

    def put(self, request, pk):
        """
        Edit status of a new picklist item
        """
        picklist_item = get_picklist_item(pk)

        if request.user.team != picklist_item.team:
            return JsonResponse(data={'errors': get_string('picklist_items.error_messages.forbidden')},
                                status=status.HTTP_403_FORBIDDEN)

        serializer = PicklistSerializer(instance=picklist_item, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'picklist_item': serializer.data})

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


