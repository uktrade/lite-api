from django.shortcuts import render
from rest_framework.views import APIView
from conf.authentication import GovAuthentication
from picklist_items.models import PicklistItem
from django.http.response import JsonResponse
from rest_framework import status


class PickListItems(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request):
        """
        Retrieve a picklist instance
        """
        picklist_items = PicklistItem.objects.filter(type='', team='')

        return JsonResponse(data={'picklist_items': picklist_items})

    def post(self, request):
        """
        Change the queues a case belongs to
        """
        return JsonResponse(data={}, status=status.HTTP_201_CREATED)


class PicklistItemDetail(APIView):

    def get(self, request, pk):
        picklist_item = PicklistItem.objects.filter(pk=pk)

        return JsonResponse(data={'picklist_item': picklist_item})
