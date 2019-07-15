from django.http import Http404

from gov_users.models import Role


def get_role_by_pk(pk):
    try:
        return Role.objects.get(pk=pk)
    except Role.DoesNotExist:
        print('Can\'t find Role')
        raise Http404