from django.http import JsonResponse, HttpResponse
from rest_framework import status

from api.applications.models import ApplicationDocument
from api.applications.serializers.document import ApplicationDocumentSerializer
from api.applications.serializers.good import DocumentOnOrganisationSerializer
from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.goodstype.document.models import GoodsTypeDocument
from api.goodstype.document.serializers import GoodsTypeDocumentSerializer
from api.parties.models import PartyDocument
from api.parties.serializers import PartyDocumentSerializer


def _get_document(documents):
    if len(documents) > 1:
        return JsonResponse(
            data={"error": "Multiple documents found for one user"}, status=status.HTTP_400_BAD_REQUEST,
        )
    elif not documents:
        return JsonResponse(data={"document": None}, status=status.HTTP_404_NOT_FOUND)
    else:
        document = documents.values()[0]
        return JsonResponse({"document": document})


def get_party_document(party):
    if not party:
        return JsonResponse(data={"error": "No such user"}, status=status.HTTP_404_NOT_FOUND)

    documents = PartyDocument.objects.filter(party=party)
    return _get_document(documents)


def get_application_document(doc_pk):
    return _get_document(ApplicationDocument.objects.filter(pk=doc_pk))


def upload_application_document(application, data, user):
    document_on_organisation = data.pop("document_on_organisation", None)

    data["application"] = application.id
    serializer = ApplicationDocumentSerializer(data=data)
    if not serializer.is_valid():
        return JsonResponse({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    document = serializer.save()

    if document_on_organisation:
        doa_serializer = DocumentOnOrganisationSerializer(
            data={
                "document": document.pk,
                "organisation": document.application.organisation.pk,
                **document_on_organisation,
            }
        )
        doa_serializer.is_valid(raise_exception=True)
        doa_serializer.save()
        audit_trail_service.create(
            actor=user.exporteruser,
            verb=AuditType.DOCUMENT_ON_ORGANISATION_CREATE,
            target=document.application.organisation,
            payload={"file_name": data.get("name")},
        )

    audit_trail_service.create(
        actor=user,
        verb=AuditType.UPLOAD_APPLICATION_DOCUMENT,
        target=application.get_case(),
        payload={"file_name": data.get("name")},
    )

    return JsonResponse({"document": serializer.data}, status=status.HTTP_201_CREATED)


def delete_application_document(document_id, application, user):
    try:
        document = ApplicationDocument.objects.get(pk=document_id)
        document.delete_s3()
        document.delete()
    except ApplicationDocument.DoesNotExist:
        return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    audit_trail_service.create(
        actor=user,
        verb=AuditType.DELETE_APPLICATION_DOCUMENT,
        target=application.get_case(),
        payload={"file_name": document.name},
    )

    return HttpResponse(status=status.HTTP_204_NO_CONTENT)


def upload_party_document(party, data, application, user):
    if not party:
        return JsonResponse(data={"error": "No such user"}, status=status.HTTP_404_NOT_FOUND)

    documents = PartyDocument.objects.filter(party=party, safe=True)
    if documents.exists():
        return JsonResponse(data={"error": "Document already exists"}, status=status.HTTP_400_BAD_REQUEST)

    data["party"] = party.id
    serializer = PartyDocumentSerializer(data=data)

    if not serializer.is_valid():
        return JsonResponse({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    # Delete existing document with a virus if one exists
    PartyDocument.objects.filter(party=party, safe=False).delete()

    serializer.save()

    audit_trail_service.create(
        actor=user,
        verb=AuditType.UPLOAD_PARTY_DOCUMENT,
        target=application.get_case(),
        action_object=serializer.instance,
        payload={"file_name": serializer.data.get("name"), "party_type": party.type, "party_name": party.name},
    )

    return JsonResponse({"document": serializer.data}, status=status.HTTP_201_CREATED)


def delete_party_document(party, application, user):
    if not party:
        return JsonResponse(data={"error": "No such user"}, status=status.HTTP_404_NOT_FOUND)

    documents = PartyDocument.objects.filter(party=party)
    for document in documents:
        document.delete_s3()
        document.delete()

        audit_trail_service.create(
            actor=user,
            verb=AuditType.DELETE_PARTY_DOCUMENT,
            target=application.get_case(),
            payload={"party_type": party.type.replace("_", " "), "party_name": party.name, "file_name": document.name},
        )

    return HttpResponse(status=status.HTTP_204_NO_CONTENT)


def get_goods_type_document(goods_type):
    if not goods_type:
        return JsonResponse(data={"error": "No such goods type"}, status=status.HTTP_400_BAD_REQUEST)

    documents = GoodsTypeDocument.objects.filter(goods_type=goods_type)
    return _get_document(documents)


def upload_goods_type_document(goods_type, data):
    if not goods_type:
        return JsonResponse(data={"error": "No such goods type"}, status=status.HTTP_400_BAD_REQUEST)

    documents = GoodsTypeDocument.objects.filter(goods_type=goods_type)
    if documents.exists():
        return JsonResponse(data={"error": "Document already exists"}, status=status.HTTP_400_BAD_REQUEST)

    data["goods_type"] = goods_type.id
    serializer = GoodsTypeDocumentSerializer(data=data)

    if not serializer.is_valid():
        return JsonResponse({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()

    return JsonResponse({"document": serializer.data}, status=status.HTTP_201_CREATED)


def delete_goods_type_document(goods_type):
    documents = GoodsTypeDocument.objects.filter(goods_type=goods_type)
    for document in documents:
        document.delete_s3()
        document.delete()

    return HttpResponse(status=status.HTTP_204_NO_CONTENT)
