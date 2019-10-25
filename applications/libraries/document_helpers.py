from django.http import JsonResponse, HttpResponse
from rest_framework import status

from applications.models import ApplicationDocument
from applications.serializers import ApplicationDocumentSerializer
from cases.libraries.activity_types import CaseActivityType
from cases.models import Case, CaseActivity
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


def get_application_documents(application_id):
    documents = ApplicationDocument.objects.filter(application__id=application_id)
    return JsonResponse({'documents': list(documents.values())})


def get_application_document(doc_pk):
    return _get_document(ApplicationDocument.objects.filter(pk=doc_pk))


def upload_application_document(application_id, data, user):
    data['application'] = application_id

    serializer = ApplicationDocumentSerializer(data=data)

    if not serializer.is_valid():
        return JsonResponse({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()

    _set_application_document_case_activity(application_id, user, data.get('name'),
                                            CaseActivityType.UPLOAD_APPLICATION_DOCUMENT)

    return JsonResponse({'document': serializer.data}, status=status.HTTP_201_CREATED)


def delete_application_document(document_id, application_id, user):
    try:
        document = ApplicationDocument.objects.get(pk=document_id)
        file_name = document.name
        document.delete_s3()
        document.delete()
    except ApplicationDocument.DoesNotExist:
        return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    _set_application_document_case_activity(application_id, user, file_name,
                                            CaseActivityType.DELETE_APPLICATION_DOCUMENT)

    return HttpResponse(status=status.HTTP_204_NO_CONTENT)


def upload_party_document(party, data, application_id, user):
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

    _set_party_document_case_activity(application_id, user, serializer.data.get('name'), party.type, party.name,
                                      CaseActivityType.UPLOAD_PARTY_DOCUMENT)

    return JsonResponse({'document': serializer.data}, status=status.HTTP_201_CREATED)


def delete_party_document(party, application_id, user):
    if not party:
        return JsonResponse(data={'error': 'No such user'}, status=status.HTTP_400_BAD_REQUEST)

    documents = PartyDocument.objects.filter(party=party)
    for document in documents:
        document.delete_s3()
        document.delete()

        _set_party_document_case_activity(application_id, user, document.name, party.type, party.name,
                                          CaseActivityType.DELETE_PARTY_DOCUMENT)

    return HttpResponse(status=204)


def _set_application_document_case_activity(application_id, user, file_name, activity_type):
    try:
        case = Case.objects.get(application__id=application_id)
    except Case.DoesNotExist:
        return

    CaseActivity.create(activity_type=activity_type,
                        case=case,
                        user=user,
                        file_name=file_name)


def _set_party_document_case_activity(application_id, user, file_name, party_type, party_name, activity_type):
    try:
        case = Case.objects.get(application__id=application_id)
    except Case.DoesNotExist:
        return

    CaseActivity.create(activity_type=activity_type,
                        case=case,
                        user=user,
                        file_name=file_name,
                        party_type=party_type.replace("_", " "),
                        party_name=party_name)
