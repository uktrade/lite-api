from django.http import Http404

from applications.models import Application


def get_application_by_pk(pk):
    try:
        return Application.objects.get(pk=pk)
    except Application.DoesNotExist:
        raise Http404
