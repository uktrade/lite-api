from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from api.applications.libraries import document_helpers
from api.applications.libraries.get_applications import get_application
from api.applications.models import ApplicationDocument
from api.applications.serializers.document import ApplicationDocumentSerializer
from api.cases.enums import CaseTypeSubTypeEnum
from api.core.authentication import ExporterAuthentication
from api.core.decorators import (
    authorised_to_view_application,
    allowed_application_types,
    application_in_state,
)
from api.goodstype.helpers import get_goods_type
from api.users.models import ExporterUser


class ApplicationDocumentView(APIView):
    """
    Retrieve or add document to an application
    """

    authentication_classes = (ExporterAuthentication,)

    @authorised_to_view_application(ExporterUser)
    def get(self, request, pk):
        """
        View all additional documents on an application
        """
        application = get_application(pk)
        documents = ApplicationDocumentSerializer(ApplicationDocument.objects.filter(application_id=pk), many=True).data

        return JsonResponse({"documents": documents, "editable": application.is_major_editable()})

    @transaction.atomic
    @authorised_to_view_application(ExporterUser)
    @application_in_state(is_editable=True)
    def post(self, request, pk):
        """
        Upload additional document onto an application
        """
        application = get_application(pk)
        return document_helpers.upload_application_document(application, request.data, request.user)


class ApplicationDocumentDetailView(APIView):
    """
    Retrieve or delete a document from an application
    """

    authentication_classes = (ExporterAuthentication,)

    @authorised_to_view_application(ExporterUser)
    def get(self, request, pk, doc_pk):
        """
        View an additional document on an application
        """
        return document_helpers.get_application_document(doc_pk)

    @transaction.atomic
    @authorised_to_view_application(ExporterUser)
    @application_in_state(is_editable=True)
    def delete(self, request, pk, doc_pk):
        """
        Delete an additional document on an application
        """
        application = get_application(pk)
        return document_helpers.delete_application_document(doc_pk, application, request.user)


class GoodsTypeDocumentView(APIView):
    """
    Retrieve, add or delete a third party document from an application
    """

    authentication_classes = (ExporterAuthentication,)

    @allowed_application_types([CaseTypeSubTypeEnum.HMRC])
    @authorised_to_view_application(ExporterUser)
    def get(self, request, pk, goods_type_pk):
        goods_type = get_goods_type(goods_type_pk)
        return document_helpers.get_goods_type_document(goods_type)

    @transaction.atomic
    @allowed_application_types([CaseTypeSubTypeEnum.HMRC])
    @application_in_state(is_major_editable=True)
    @authorised_to_view_application(ExporterUser)
    def post(self, request, pk, goods_type_pk):
        goods_type = get_goods_type(goods_type_pk)
        return document_helpers.upload_goods_type_document(goods_type, request.data)

    @transaction.atomic
    @allowed_application_types([CaseTypeSubTypeEnum.HMRC])
    @authorised_to_view_application(ExporterUser)
    def delete(self, request, pk, goods_type_pk):
        goods_type = get_goods_type(goods_type_pk)
        if not goods_type:
            return JsonResponse(data={"error": "No such goods type"}, status=status.HTTP_400_BAD_REQUEST)

        return document_helpers.delete_goods_type_document(goods_type)
