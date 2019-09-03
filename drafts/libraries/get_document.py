from django.http import Http404, JsonResponse
from rest_framework import status

from drafts.libraries.get_draft import get_draft
from end_user.document.models import EndUserDocument


def get_document(document_id, draft_id):
    try:
        draft = get_draft(draft_id)
        end_user = draft.end_user
        if end_user is None:
            return JsonResponse(data={'error': 'No such user'},
                                status=status.HTTP_400_BAD_REQUEST)

        documents = EndUserDocument.objects.filter(id=document_id, end_user=end_user)
        if len(documents) > 1:
            return JsonResponse(data={'error': 'Multiple documents found for one end user'},
                                status=status.HTTP_400_BAD_REQUEST)
        elif len(documents) == 0:
            return JsonResponse(data={'error': 'No document found'},
                                status=status.HTTP_404_NOT_FOUND)
        else:
            document = documents.first()
            return JsonResponse({'document': document})

    except EndUserDocument.DoesNotExist:
        raise Http404
