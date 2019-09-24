from django.http import Http404

from applications.models import Application
from goods.models import Good


def get_applications():
    return Application.objects.filter(submitted_at__isnull=False)


def get_applications_with_organisation(organisation):
    return Application.objects.filter(organisation=organisation, submitted_at__isnull=False)


def get_application(pk):
    try:
        return Application.objects.get(pk=pk, submitted_at__isnull=False)
    except Application.DoesNotExist:
        raise Http404


def get_application_with_organisation(pk, organisation):
    try:
        draft = Application.objects.get(pk=pk, submitted_at__isnull=False)

        if draft.organisation.pk != organisation.pk:
            raise Http404

        return draft
    except Application.DoesNotExist:
        raise Http404


def get_good_with_organisation(pk, organisation):
    try:
        good = Good.objects.get(pk=pk)

        if good.organisation.pk != organisation.pk:
            raise Http404

        return good
    except Good.DoesNotExist:
        raise Http404
