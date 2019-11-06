from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView

from applications.enums import ApplicationType
from applications.libraries.document_helpers import upload_application_document, delete_application_document, \
    get_application_document, get_application_documents, upload_goods_type_document, delete_goods_type_document, \
    get_goods_type_document
from applications.serializers.document import ApplicationDocumentSerializer
from conf.authentication import ExporterAuthentication
from conf.decorators import authorised_users, allowed_application_types, application_in_major_editable_state
from goodstype.document.serializers import GoodsTypeDocumentSerializer
from goodstype.helpers import get_goods_type
from users.models import ExporterUser


class ApplicationDocumentView(APIView):
    """
    Retrieve or add document to an application
    """
    authentication_classes = (ExporterAuthentication,)

    @authorised_users(ExporterUser)
    def get(self, request, application):
        """
        View all additional documents on an application
        """
        return get_application_documents(application)

    @swagger_auto_schema(
        request_body=ApplicationDocumentSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic
    @authorised_users(ExporterUser)
    def post(self, request, application):
        """
        Upload additional document onto an application
        """
        return upload_application_document(application, request.data, request.user)


class ApplicationDocumentDetailView(APIView):
    """
    Retrieve or delete a document from an application
    """
    authentication_classes = (ExporterAuthentication,)

    @authorised_users(ExporterUser)
    def get(self, request, application, doc_pk):
        """
        View an additional document on an application
        """
        return get_application_document(doc_pk)

    @swagger_auto_schema(
        request_body=ApplicationDocumentSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic
    @authorised_users(ExporterUser)
    def delete(self, request, application, doc_pk):
        """
        Delete an additional document on an application
        """
        return delete_application_document(doc_pk, application, request.user)


class GoodsTypeDocumentView(APIView):
    """
    Retrieve, add or delete a third party document from an application
    """
    authentication_classes = (ExporterAuthentication,)

    @allowed_application_types(ApplicationType.HMRC_QUERY)
    @authorised_users(ExporterUser)
    def get(self, request, application, goods_type_pk):
        goods_type = get_goods_type(goods_type_pk)
        return get_goods_type_document(goods_type)

    @swagger_auto_schema(
        request_body=GoodsTypeDocumentSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic
    @allowed_application_types(ApplicationType.HMRC_QUERY)
    @application_in_major_editable_state()
    @authorised_users(ExporterUser)
    def post(self, request, application, goods_type_pk):
        goods_type = get_goods_type(goods_type_pk)
        return upload_goods_type_document(goods_type, request.data)

    @swagger_auto_schema(
        request_body=GoodsTypeDocumentSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic
    @allowed_application_types(ApplicationType.HMRC_QUERY)
    @authorised_users(ExporterUser)
    def delete(self, request, application, goods_type_pk):
        goods_type = get_goods_type(goods_type_pk)
        return delete_goods_type_document(goods_type)
