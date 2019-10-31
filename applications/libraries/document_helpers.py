from django.http import JsonResponse, HttpResponse
from rest_framework import status

from applications.libraries.case_activity import set_party_document_case_activity, \
    set_application_document_case_activity
from applications.models import ApplicationDocument
from applications.serializers.serializers import ApplicationDocumentSerializer
from cases.libraries.activity_types import CaseActivityType
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


def get_application_documents(application):
    documents = ApplicationDocument.objects.filter(application=application)
    return JsonResponse({'documents': list(documents.values())})


def get_application_document(doc_pk):
    return _get_document(ApplicationDocument.objects.filter(pk=doc_pk))


def upload_application_document(application, data, user):
    data['application'] = application.id

    serializer = ApplicationDocumentSerializer(data=data)

    if not serializer.is_valid():
        return JsonResponse({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()

    set_application_document_case_activity(CaseActivityType.UPLOAD_APPLICATION_DOCUMENT, data.get('name'), user,
                                           application)

    return JsonResponse({'document': serializer.data}, status=status.HTTP_201_CREATED)


def delete_application_document(document_id, application, user):
    try:
        document = ApplicationDocument.objects.get(pk=document_id)
        file_name = document.name
        document.delete_s3()
        document.delete()
    except ApplicationDocument.DoesNotExist:
        return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    set_application_document_case_activity(CaseActivityType.DELETE_APPLICATION_DOCUMENT, file_name, user, application)

    return HttpResponse(status=status.HTTP_204_NO_CONTENT)


def upload_party_document(party, data, application, user):
    if not party:
        return JsonResponse(data={'error': 'No such user'}, status=status.HTTP_400_BAD_REQUEST)

    documents = PartyDocument.objects.filter(party=party)
    if documents:
        return JsonResponse(data={'error': 'Document already exists'}, status=status.HTTP_400_BAD_REQUEST)

    data['party'] = party.id
    serializer = PartyDocumentSerializer(data=data)

    if not serializer.is_valid():
        return JsonResponse({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()

    set_party_document_case_activity(CaseActivityType.UPLOAD_PARTY_DOCUMENT, serializer.data.get('name'), party.type,
                                     party.name, user, application)

    return JsonResponse({'document': serializer.data}, status=status.HTTP_201_CREATED)


def delete_party_document(party, application, user):
    if not party:
        return JsonResponse(data={'error': 'No such user'}, status=status.HTTP_400_BAD_REQUEST)

    documents = PartyDocument.objects.filter(party=party)
    for document in documents:
        document.delete_s3()
        document.delete()

        set_party_document_case_activity(CaseActivityType.DELETE_PARTY_DOCUMENT, document.name, party.type,
                                         party.name, user, application)

    return HttpResponse(status=status.HTTP_204_NO_CONTENT)
