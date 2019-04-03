from django.http import JsonResponse, Http404
from rest_framework import status, permissions
from rest_framework.decorators import permission_classes
from rest_framework.views import APIView

from applications.models import Application
from applications.serializers import ApplicationBaseSerializer
from applications.libraries.ApplicationStatuses import ApplicationStatuses


@permission_classes((permissions.AllowAny,))
class ApplicationList(APIView):
    """
    List all applications, or create a new application from a draft.
    """
    def get(self, request):
        applications = Application.objects.filter(draft=False).order_by('name')
        serializer = ApplicationBaseSerializer(applications, many=True)
        return JsonResponse(data={'status': 'success', 'applications': serializer.data},
                            safe=False)

    def post(self, request):
        submit_id = request.POST.get('id', None)

        # Get Draft
        try:
            draft = Application.objects.get(pk=submit_id)
            if not draft.draft:
                raise Http404
        except Application.DoesNotExist:
            raise Http404

        draft.status = ApplicationStatuses.SUBMITTED

        # Remove draft tag
        draft.draft = False
        draft.save()

        # Return application
        serializer = ApplicationBaseSerializer(draft)
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
            if application.draft:
                raise Http404
            return application
        except Application.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        application = self.get_object(pk)
        serializer = ApplicationBaseSerializer(application)
        return JsonResponse(data={'status': 'success', 'application': serializer.data})
