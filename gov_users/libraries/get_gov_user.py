from django.http import Http404

from gov_users.models import GovUser


def get_gov_user_by_pk(pk):
    try:
        return GovUser.objects.get(pk=pk)
    except GovUser.DoesNotExist:
        raise Http404