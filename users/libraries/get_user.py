from conf.exceptions import NotFoundError
from users.models import ExporterUser, GovUser


def get_user_by_pk(pk):
    """
    Returns either an ExporterUser or a GovUser depending on the PK given
    """
    try:
        return ExporterUser.objects.get(pk=pk)
    except ExporterUser.DoesNotExist:
        try:
            return GovUser.objects.get(pk=pk)
        except GovUser.DoesNotExist:
            raise NotFoundError({'user': 'User not found - ' + str(pk)})
