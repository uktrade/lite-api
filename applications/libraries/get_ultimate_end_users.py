from applications.models import Application
from drafts.models import Draft
from parties.models import UltimateEndUser


def get_ultimate_end_users(obj):
    if isinstance(object, Application):
        return UltimateEndUser.objects.filter(application=obj)
    elif isinstance(object, Draft):
        return UltimateEndUser.objects.filter(draft=obj)
    else:
        return list()
