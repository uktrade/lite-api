from django.http import Http404

from applications.models import AbstractApplication
from goods.models import Good


def get_drafts():
    return AbstractApplication.objects.filter(submitted_at__isnull=True)


def get_drafts_with_organisation(organisation):
    return AbstractApplication.objects.filter(organisation=organisation, submitted_at__isnull=True)


def get_draft(pk):
    try:
        return AbstractApplication.objects.get(pk=pk, submitted_at__isnull=True)
    except AbstractApplication.DoesNotExist:
        raise Http404


def get_draft_with_organisation(pk, organisation):
    try:
        draft = AbstractApplication.objects.get(pk=pk, submitted_at__isnull=True)

        if draft.organisation.pk != organisation.pk:
            raise Http404

        return draft
    except AbstractApplication.DoesNotExist:
        raise Http404


def get_good_with_organisation(pk, organisation):
    try:
        good = Good.objects.get(pk=pk)

        if good.organisation.pk != organisation.pk:
            raise Http404

        return good
    except Good.DoesNotExist:
        raise Http404
