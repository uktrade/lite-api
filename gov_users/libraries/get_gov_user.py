from django.http import Http404

from gov_users.models import GovUser


def get_gov_user_by_pk(pk):
    try:
        return GovUser.objects.get(pk=pk)
    except GovUser.DoesNotExist:
        print('Can\'t find GOV User')
        raise Http404


def get_gov_user_by_email(email):
    try:
        return GovUser.objects.get(email=email)
    except GovUser.DoesNotExist:
        print('Can\'t find GOV User')
        raise Http404
