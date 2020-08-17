from django.http import Http404

from api.conf.exceptions import NotFoundError
from flags.models import Flag, FlaggingRule


def get_flag(pk):
    try:
        return Flag.objects.get(pk=pk)
    except Flag.DoesNotExist:
        raise Http404


def get_flagging_rule(pk):
    try:
        return FlaggingRule.objects.get(pk=pk)
    except FlaggingRule.DoesNotExist:
        raise NotFoundError({"flagging_rule": "Flagging rule not found - " + str(pk)})
