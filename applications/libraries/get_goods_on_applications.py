from django.http import Http404

from applications.models import GoodOnApplication


def get_good_on_application(pk):
    try:
        return GoodOnApplication.objects.get(pk=pk)
    except GoodOnApplication.DoesNotExist:
        raise Http404
