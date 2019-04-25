from django.http import Http404

from drafts.models import Draft
from goods.models import Good


def get_draft(pk):
    try:
        return Draft.objects.get(pk=pk)
    except Draft.DoesNotExist:
        raise Http404


def get_draft_with_organisation(pk, organisation):
    try:
        draft = Draft.objects.get(pk=pk)

        if draft.organisation.pk != organisation.pk:
            raise Http404

        return draft
    except Draft.DoesNotExist:
        raise Http404


def get_good_with_organisation(pk, organisation):
    try:
        good = Good.objects.get(pk=pk)

        if good.organisation.pk != organisation.pk:
            raise Http404

        return good
    except Good.DoesNotExist:
        raise Http404