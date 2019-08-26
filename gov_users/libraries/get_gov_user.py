from conf.exceptions import NotFoundError
from users.models import GovUser


def get_gov_user_by_email(email):
    try:
        return GovUser.objects.get(email=email)
    except GovUser.DoesNotExist:
        raise NotFoundError({'user': 'User not found'})
