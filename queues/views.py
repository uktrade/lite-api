from django.db import transaction
from django.http import JsonResponse, Http404
from rest_framework import permissions, status
from rest_framework.decorators import permission_classes
from rest_framework.parsers import JSONParser
from rest_framework.utils import json
from rest_framework.views import APIView

from cases.models import CaseAssignment
from conf.authentication import GovAuthentication
from queues.libraries.get_queue import get_queue
from queues.models import Queue
from queues.serializers import QueueSerializer, QueueViewSerializer, CaseAssignmentSerializer


@permission_classes((permissions.AllowAny,))
class QueuesList(APIView):
    """
    List all queues
    """
    authentication_classes = (GovAuthentication,)

    def get(self, request):
        queues = Queue.objects.filter().order_by('name')
        serializer = QueueViewSerializer(queues, many=True)
        return JsonResponse(data={'queues': serializer.data})

    def post(self, request):
        data = JSONParser().parse(request)
        serializer = QueueSerializer(data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'queue': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


@permission_classes((permissions.AllowAny,))
class QueueDetail(APIView):
    """
    Retrieve a queue instance
    """
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        queue = get_queue(pk)
        serializer = QueueViewSerializer(queue)
        return JsonResponse(data={'queue': serializer.data})

    def put(self, request, pk):
        queue = get_queue(pk)
        data = request.data.copy()
        serializer = QueueSerializer(instance=queue, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'queue': serializer.data})
        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class CaseAssignments(APIView):
    """
    Update users to case assignments on a queue
    """

    @transaction.atomic
    def post(self, request, pk):
        queue = get_queue(pk)
        data = request.data

        responses = []
        errors = []
        for assignment in data['assignments']:
            user = assignment['user']
            case = assignment['case']
            assignment['queue'] = queue.id
            serializer = CaseAssignmentSerializer(data=assignment)
            if serializer.is_valid():
                try:
                    CaseAssignment.objects.get(user=user, case=case, queue=queue)

                except CaseAssignment.DoesNotExist:
                    serializer.save()

                responses.append({'case_assignment': serializer.data})
            else:
                errors.append({'errors': serializer.errors})

        if len(errors) > 0:
            return JsonResponse(data=errors, status=status.HTTP_400_BAD_REQUEST, safe=False)

        return JsonResponse(data=responses, status=status.HTTP_200_OK, safe=False)

    @transaction.atomic
    def put(self, request, pk):
        queue = get_queue(pk)
        data = request.data

        responses = []
        errors = []
        CaseAssignment.objects.filter(queue=queue).delete()
        for assignment in data['assignments']:
            assignment['queue'] = queue.id
            serializer = CaseAssignmentSerializer(data=assignment)
            if serializer.is_valid():
                serializer.save()
                responses.append({'case_assignment': serializer.data})
            else:
                errors.append({'errors': serializer.errors})

        if len(errors) > 0:
            return JsonResponse(data=errors, status=status.HTTP_400_BAD_REQUEST, safe=False)

        return JsonResponse(data=responses, status=status.HTTP_200_OK, safe=False)
