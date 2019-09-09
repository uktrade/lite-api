from applications.models import Application
from drafts.models import Draft
from parties.models import UltimateEndUser


def get_ultimate_end_users(obj):
    if isinstance(obj, Application):
        return UltimateEndUser.objects.filter(application=obj)
    elif isinstance(obj, Draft):
        return UltimateEndUser.objects.filter(draft=obj)
    else:
        return list()
