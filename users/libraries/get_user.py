from django.http import Http404

from conf.exceptions import NotFoundError
from users.models import ExporterUser, GovUser


def get_user_by_pk(pk):
    try:
        return ExporterUser.objects.get(pk=pk)
    except ExporterUser.DoesNotExist:
        try:
            return GovUser.objects.get(pk=pk)
        except GovUser.DoesNotExist:
            raise NotFoundError({'user': 'User not found - ' + str(pk)})


def get_user_by_email(email):
    try:
        return ExporterUser.objects.get(email=email)
    except ExporterUser.DoesNotExist:
        raise Http404
