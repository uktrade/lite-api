from django.http import JsonResponse, Http404
from django.shortcuts import redirect
from rest_framework import status, permissions
from rest_framework.decorators import permission_classes
from rest_framework.views import APIView

from applications.models import Application, Good, Destination
from applications.serializers import ApplicationSerializer
from conf.settings import JSON_INDENT


@permission_classes((permissions.AllowAny,))
class ApplicationList(APIView):
    """
    List all applications, or create a new application from a draft.
    """
    def get(self, request):
        applications = Application.objects.filter(draft=False)
        serializer = ApplicationSerializer(applications, many=True)
        return JsonResponse(data={'status': 'success', 'applications': serializer.data},
                            json_dumps_params={'indent': JSON_INDENT}, safe=False)

    def post(self, request):
        submit_id = request.POST.get('id', None)

        # Get Draft
        try:
            draft = Application.objects.get(pk=submit_id)
            if not draft.draft:
                raise Http404
        except Application.DoesNotExist:
            raise Http404

        # Remove draft tag
        draft.draft = False
        draft.save()

        # Return application
        serializer = ApplicationSerializer(draft)
        return JsonResponse(data={'status': 'success', 'application': serializer.data},
                            json_dumps_params={'indent': JSON_INDENT}, status=status.HTTP_201_CREATED)


@permission_classes((permissions.AllowAny,))
class ApplicationDetail(APIView):
    """
    Retrieve, update or delete a application instance.
    """
    def get_object(self, pk):
        try:
            application = Application.objects.get(pk=pk)
            if application.draft:
                raise Http404
            return application
        except Application.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        application = self.get_object(pk)
        serializer = ApplicationSerializer(application)
        return JsonResponse(data={'status': 'success', 'application': serializer.data},
                            json_dumps_params={'indent': JSON_INDENT})


@permission_classes((permissions.AllowAny,))
class TestData(APIView):
    """
    Create test data
    """

    def get(self, request):

        application = Application(user_id='123',
                                  name='Lemonworld',
                                  draft=False)
        application.save()

        good = Good(name='Lemon',
                    description='big slice of lemon',
                    quantity=4,
                    control_code='lem0n',
                    application=application)
        good.save()

        destination = Destination(name='Ohio',
                                  application=application)
        destination.save()

        applications = Application.objects.filter(draft=False)
        serializer = ApplicationSerializer(applications, many=True)
        return JsonResponse(data={'status': 'success', 'applications': serializer.data},
                            json_dumps_params={'indent': JSON_INDENT}, safe=False)
