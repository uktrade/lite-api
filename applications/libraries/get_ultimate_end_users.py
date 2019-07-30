from end_user.models import EndUser


def get_ultimate_end_user_ids(obj):
    ultimate_end_users_ids = obj.ultimate_end_users.values_list('id', flat=True)
    ultimate_end_users = []
    for id in ultimate_end_users_ids:
        ultimate_end_users.append(EndUser.objects.get(id=str(id)))

    return ultimate_end_users