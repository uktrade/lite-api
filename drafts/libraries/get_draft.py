from django.http import Http404, HttpResponse

from drafts.models import Draft


def get_draft(self, pk):
    try:
        return Draft.objects.get(pk=pk)
    except Draft.DoesNotExist:
        raise Http404


def get_draft_with_organisation(self, pk, organisation):
    try:
        draft = Draft.objects.get(pk=pk)

        if draft.organisation is not organisation:
            raise HttpResponse(status=403)

        return draft
    except Draft.DoesNotExist:
        raise Http404
