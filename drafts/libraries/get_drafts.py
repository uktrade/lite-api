from django.http import Http404

from applications.models import Application
from goods.models import Good


def get_drafts():
    return Application.objects.filter(submitted_at__isnull=True)


def get_drafts_with_organisation(organisation):
    return Application.objects.filter(submitted_at__isnull=True, organisation=organisation)


def get_draft(pk):
    try:
        return Application.objects.get(pk=pk, submitted_at__isnull=True)
    except Application.DoesNotExist:
        raise Http404


def get_draft_with_organisation(pk, organisation):
    try:
        draft = Application.objects.get(pk=pk, submitted_at__isnull=True)

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
