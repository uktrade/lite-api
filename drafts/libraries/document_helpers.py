from django.http import JsonResponse, HttpResponse
from rest_framework import status

from drafts.models import DraftDocuments
from drafts.serializers import DraftDocumentsSerializer
from parties.document.models import PartyDocument
from parties.document.serializers import PartyDocumentSerializer


def _get_document(documents):
    if len(documents) > 1:
        return JsonResponse(data={'error': 'Multiple documents found for one user'},
                            status=status.HTTP_400_BAD_REQUEST)
    elif not documents:
        return JsonResponse(data={'document': None},
                            status=status.HTTP_404_NOT_FOUND)
    else:
        document = documents.values()[0]
        return JsonResponse({'document': document})


def get_party_document(party):
    if not party:
        return JsonResponse(data={'error': 'No such user'}, status=status.HTTP_400_BAD_REQUEST)

    documents = PartyDocument.objects.filter(party=party)
    return _get_document(documents)


def get_draft_documents(draft_id):
    documents = DraftDocuments.objects.filter(draft=draft_id)
    return JsonResponse({'documents': list(documents.values())})


def get_draft_document(draft_id, doc_pk):
    return _get_document(DraftDocuments.objects.filter(draft=draft_id, id=doc_pk))


def upload_draft_document(draft_id, data):
    data['draft'] = draft_id

    serializer = DraftDocumentsSerializer(data=data)

    if serializer.is_valid():
        serializer.save()
        return JsonResponse({'document': serializer.data}, status=status.HTTP_201_CREATED)
    else:
        return JsonResponse({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


def delete_draft_document(document_id):
    try:
        document = DraftDocuments.objects.get(id=document_id)
        document.delete_s3()
        document.delete()
    except DraftDocuments.DoesNotExist:
        return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    return HttpResponse(status=status.HTTP_204_NO_CONTENT)


def upload_party_document(party, data):
    if not party:
        return JsonResponse(data={'error': 'No such user'}, status=status.HTTP_400_BAD_REQUEST)

    documents = PartyDocument.objects.filter(party=party)
    if documents:
        return JsonResponse(data={'error': 'Document already exists'}, status=status.HTTP_400_BAD_REQUEST)

    data['party'] = party.id
    serializer = PartyDocumentSerializer(data=data)

    if serializer.is_valid():
        serializer.save()
        return JsonResponse({'document': serializer.data}, status=status.HTTP_201_CREATED)
    else:
        return JsonResponse({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


def delete_party_document(party):
    if not party:
        return JsonResponse(data={'error': 'No such user'}, status=status.HTTP_400_BAD_REQUEST)

    documents = PartyDocument.objects.filter(party=party)
    for document in documents:
        document.delete_s3()
        document.delete()

    return HttpResponse(status=204)
