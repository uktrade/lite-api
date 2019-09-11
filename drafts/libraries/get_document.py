from django.http import Http404, JsonResponse
from rest_framework import status

from end_user.document.models import EndUserDocument


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
            return JsonResponse(data={'document': None},
                                status=status.HTTP_404_NOT_FOUND)
        else:
            document = documents.values()[0]
            return JsonResponse({'document': document})

    except EndUserDocument.DoesNotExist:
        raise Http404
