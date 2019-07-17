from django.http import Http404

from users.models import ExporterUser


def get_user_by_pk(pk):
    try:
        return ExporterUser.objects.get(pk=pk)
    except ExporterUser.DoesNotExist:
        raise Http404


def get_user_by_email(email):
    try:
        return ExporterUser.objects.get(email=email)
    except ExporterUser.DoesNotExist:
        raise Http404
