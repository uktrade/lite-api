from django.http import Http404

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
        raise Http404
