from conf.exceptions import NotFoundError
from gov_users.models import Role


def get_role_by_pk(pk):
    try:
        return Role.objects.get(pk=pk)
    except Role.DoesNotExist:
        raise NotFoundError({'role': 'Role not found'})
