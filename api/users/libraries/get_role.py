from api.core.exceptions import NotFoundError
from api.users.models import Role


def get_role_by_pk(pk, organisation=None):
    try:
        return Role.objects.get(pk=pk, organisation=organisation)
    except Role.DoesNotExist:
        raise NotFoundError({"role": "Role not found"})
