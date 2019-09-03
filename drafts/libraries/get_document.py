from django.http import Http404, JsonResponse
from rest_framework import status

from drafts.libraries.get_draft import get_draft
from end_user.document.models import EndUserDocument
from end_user.models import EndUser


def get_document(end_user):
    try:
        if end_user is None:
            return JsonResponse(data={'error': 'No such user'},
                                status=status.HTTP_400_BAD_REQUEST)

        documents = EndUserDocument.objects.filter(end_user=end_user)
        if len(documents) > 1:
            return JsonResponse(data={'error': 'Multiple documents found for one end user'},
                                status=status.HTTP_400_BAD_REQUEST)
        elif not documents:
            return JsonResponse(data={'error': 'No document found'},
                                status=status.HTTP_404_NOT_FOUND)
        else:
            document = documents.values()[0]
            return JsonResponse({'document': document})

    except EndUserDocument.DoesNotExist:
        raise Http404


def get_end_user_document(draft_id):
    draft = get_draft(draft_id)
    end_user = draft.end_user
    return get_document(end_user)


def get_ultimate_end_user_document(ueu_id):
    end_user = EndUser.objects.filter(id=str(ueu_id)).first()
    return get_document(end_user)
