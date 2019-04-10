from django.db import transaction
from django.http import JsonResponse, Http404
from rest_framework import status, permissions
from rest_framework.decorators import permission_classes
import json
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from applications.models import Application, ApplicationStatuses
from applications.serializers import ApplicationBaseSerializer, ApplicationCreateSerializer, ApplicationUpdateSerializer

from cases.models import Case
from drafts.models import Draft
from queues.models import Queue

import reversion


@permission_classes((permissions.AllowAny,))
class ApplicationList(APIView):
    """
    List all applications, or create a new application from a draft.
    """
    def get(self, request):
        applications = Application.objects.order_by('created_at')
        serializer = ApplicationBaseSerializer(applications, many=True)
        return JsonResponse(data={'status': 'success', 'applications': serializer.data},
                            safe=False)

    @transaction.atomic
    def post(self, request):
        submit_id = json.loads(request.body).get('id')

        with reversion.create_revision():

            # Get Draft
            try:
                draft = Draft.objects.get(pk=submit_id)
            except Draft.DoesNotExist:
                raise Http404

            # Create an Application object corresponding to the draft

            application = Application(id=draft.id,
                                      user_id=draft.user_id,
                                      name=draft.name,
                                      control_code=draft.control_code,
                                      activity=draft.activity,
                                      destination=draft.destination,
                                      usage=draft.usage,
                                      created_at=draft.created_at,
                                      last_modified_at=draft.last_modified_at,
                                      submitted_at=draft.submitted_at
                                      )

            application.save()
            # Store some meta-information.
            # reversion.set_user(request.user)          # No user information yet
            reversion.set_comment("Created Application Revision")

            # Create a case
            case = Case(application=application)
            case.save()

            # Add said case to default queue
            queue = Queue.objects.get(pk='00000000-0000-0000-0000-000000000001')
            queue.cases.add(case)
            queue.save()

            serializer = ApplicationBaseSerializer(application)
            return JsonResponse(data={'status': 'success', 'application': serializer.data},
                                    status=status.HTTP_201_CREATED)


@permission_classes((permissions.AllowAny,))
class ApplicationDetail(APIView):
    """
    Retrieve, update or delete a application instance.
    """
    def get_object(self, pk):
        try:
            application = Application.objects.get(pk=pk)
            return application
        except Application.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        application = self.get_object(pk)
        serializer = ApplicationBaseSerializer(application)
        return JsonResponse(data={'status': 'success', 'application': serializer.data})

    def put(self, request, pk):
        data = JSONParser().parse(request)
        serializer = ApplicationUpdateSerializer(self.get_object(pk), data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'status': 'success', 'application': serializer.data},
                                status=status.HTTP_200_OK)
        return JsonResponse(data={'status': 'error', 'errors': serializer.errors},
                            status=400)
