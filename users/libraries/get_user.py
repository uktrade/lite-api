from django.http import Http404

from users.models import User


def get_user_by_pk(pk):
    try:
        return User.objects.get(pk=pk)
    except User.DoesNotExist:
        raise Http404


def get_user_by_email(email):
    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        raise Http404
